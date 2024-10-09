from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_brand_id = fields.Many2one("akustikken.product.brand", "Product Brand", related='product_tmpl_id.product_brand_id', store=True)
    product_series_id = fields.Many2one("akustikken.product.series", "Product Series", related='product_tmpl_id.product_series_id', ondelete="restrict", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        sale_tax_ids = [Command.link(company.account_sale_tax_id.id) for company in self.env['res.company'].sudo().search([('account_sale_tax_id', '!=', False)])]
        supplier_taxes_ids = [Command.link(company.account_purchase_tax_id.id) for company in self.env['res.company'].sudo().search([('account_purchase_tax_id', '!=', False)])]
        products = super(ProductProduct, self.with_context(create_product_product=True)).create(vals_list)

        for product in products.sudo():
            product.update({
                'taxes_id': sale_tax_ids,
                'supplier_taxes_id': supplier_taxes_ids
            })
        return products

    def create_product(self, product_data, company=False):
        """ Creates a single product from a dictionary of information. See required information in trunk_endpoint_sale/documentation/product
        Supplierinfo and routes are always updated.
        If product does exist, we update it.
        If product does not exist, we create it with the values from product_data
        :param dict product_data : Information about the product
        :param company : company that are creating the product. Used to handle supplierinfo.
        :return integer : id of new or exisiting product
        :
        """
        existing_product = self.find_existing_product(product_data)
        is_produced = self.is_production_product(product_data)
        supplier = self._get_product_supplier(product_data)
        if existing_product:
            # Make sure that existing products also have supplier info.
            if supplier:
                self._handle_supplierinfo(product_data, existing_product, supplier, is_produced, company)
            # Update routes every time
            existing_product.write({
                'route_ids': self._prepare_route_values(product_data, supplier, is_produced, existing_product),
                # 'property_account_expense_id': False,
                # 'property_account_income_id': False
            })
            # existing_product.product_tmpl_id.property_account_expense_id = False
            # existing_product.product_tmpl_id.property_account_income_id = False
            return existing_product.id
        values = self._prepare_values(product_data, supplier, is_produced)
        main_product = False
        # If there is not any existing products already, then create a product.
        main_product = self.env['product.product'].sudo().create(values)
        # if there is a product(s), then check if the product(s) should be updated.
        # if existing_product:
        #     if product_data.get('update', False):
        #         existing_product.sudo().write(values)
        #         main_product = existing_product

        if main_product and supplier:
            self._handle_supplierinfo(product_data, main_product, supplier, is_produced, company)
        if product_data.get('bom'):
            self._create_product_bom(product_data['bom'], main_product, product_data.get('update'), product_data.get('manufacturing_time'))

        # Update logic is currently not in use by customer. They don't know if a product already exists in Odoo. Update is always true.
        # if 'update' in product_data:
        #     if not product_data['update']:
        #         return existing_product.id

        # Brand and series has to be written to product template with this function.
        self.handle_brand_series(product_data, main_product)

        main_product.property_account_expense_id = False
        main_product.property_account_income_id = False
        main_product.product_tmpl_id.property_account_expense_id = False
        main_product.product_tmpl_id.property_account_income_id = False

        return main_product.id

    def find_existing_product(self, product_data):
        """We use reference and supplier code to find the product.supplierinfo record
        If there is not supplier record here we check the supplier records for the production production company(strai kjøkken)
        If there is no supplier record in either of those, we conclude that the product does not exist.
        This means, that if the same product gets imported with a different reference, it will be created twice on product.template
        :param dict product_data : Information about the product
        :returns recordset of product.product or bool False
        """
        supplier_code = product_data.get('supplier_code', False)
        if not supplier_code:
            # Get supplier or create if not exists
            supplier_code = self.get_or_create_no_supplier_partner_ref().ref

        # handle cases where the partner have been archived by a manual mistake
        supplier_id = self.env['res.partner'].with_context(active_test=False).search([('ref', '=', supplier_code)])
        if len(supplier_id) > 1:
            raise ValidationError(_("Error: More than one supplier found: {}".format(supplier_id)))
        if not product_data.get('reference') and supplier_id and supplier_id.id:
            product_data['reference'] = 'DIV'
        if product_data.get('reference'):
            # suppliers = self.env['product.supplierinfo'].sudo().search([('product_code', '=', product_data['reference']), ('partner_id', '=', supplier_id.id)])
            # First check if there is a supplier reference for the current company
            suppliers = self.env['product.supplierinfo'].search([('winner_product_code', '=', product_data['reference']), ('partner_id', '=', supplier_id.id)])
            # If there is no supplier ref for the current company, check if the production company has a supplier ref for it.
            if not suppliers:
                production_company = self.env['res.company'].search([('production', '=', True)])
                suppliers = self.env['product.supplierinfo'].with_company(production_company).search([('winner_product_code', '=', product_data['reference']), ('partner_id', '=', supplier_id.id)])
                # manual error when importing new products, sometimes the person forgets to set the winner_product_code field
                if not suppliers:
                    suppliers = self.env['product.supplierinfo'].with_company(production_company).search([('product_code', '=', product_data['reference']), ('partner_id', '=', supplier_id.id)])
                    if suppliers:
                        suppliers.write({
                            'winner_product_code': product_data['reference']
                        })
            if len(suppliers.product_tmpl_id.with_context(active_test=False).product_variant_ids) > 1:
                raise ValidationError(_("Error: supplier_code={}, reference={} | Has found more than one: {} {} {}".format(supplier_code, product_data['reference'], suppliers, suppliers.product_tmpl_id.product_variant_ids, suppliers.product_tmpl_id)))
            # manual errors when people archive products in Odoo that are actually still in use
            return suppliers.product_tmpl_id.with_context(active_test=False).product_variant_ids
        return False

    def handle_brand_series(self, product_data, main_product):
        """Writes brand or brand and series to product record.
        if brand is not in product_data, it will do nothing.
        :param dict product_data : Information about the product
        :param recordset product.product
        """
        brand_series_values = {}
        brand_id = False
        if 'brand' in product_data:
            if product_data.get('brand'):
                brand_id = self.env['akustikken.product.brand'].search([('name', '=', product_data.get('brand'))], limit=1)
                if not brand_id:
                    brand_id = self.env['akustikken.product.brand'].create({'name': product_data.get('brand')})
                brand_series_values['product_brand_id'] = brand_id.id
                main_product.product_tmpl_id.sudo().write(brand_series_values)
        if 'series' in product_data:
            if product_data.get('series') and brand_id:
                series_id = self.env['akustikken.product.series'].search([('name', '=', product_data.get('series'))], limit=1)
                if not series_id:
                    series_id = self.env['akustikken.product.series'].create({'name': product_data.get('series'),
                                                                              'product_brand_id': brand_id.id})
                brand_series_values['product_series_id'] = series_id.id
                main_product.product_tmpl_id.sudo().write(brand_series_values)

    def _create_product_bom(self, bom_data, product, update, manufacturing_time):
        if update and product.bom_ids:
            product.bom_ids.write({'active': False})
        bom = self.env['mrp.bom'].create({'product_id': product.id,
                                          'product_tmpl_id': product.product_tmpl_id.id,
                                          'produce_delay': manufacturing_time or 0})
        for line in bom_data:
            self.env['mrp.bom.line'].create({'bom_id': bom.id,
                                             'product_id': self._create_product(line['product']),
                                             'product_qty': line['quantity']})

    def get_or_create_no_supplier_partner_ref(self):
        # TODO correct this to find correct seller, do not create more every time
        supplier_ids = self.env['res.partner'].search([('ref', '=', 'no_supplier')])
        if not supplier_ids:
            supplier_ids = self.env['res.partner'].create({'name': '*Mangler Leverandør*',
                                                           'ref': 'no_supplier'})
        return supplier_ids

    def _prepare_values(self, product_data, supplier, is_produced):
        """Prepare values from product_data into correct values dict format and return the dict
        :param dict product_data : Information about the product
        :param recordset supplier : res.partner
        :returns : dict of correctly formated product values
        """

        values = {}
        # Required
        values['name'] = product_data['name']
        # values['default_code'] = product_data.get('reference')
        values['categ_id'] = self.get_category_id(product_data["product_category"]) or self.env.ref('product.product_category_all').id

        # Optional
        values['description'] = product_data.get('description')
        values['list_price'] = product_data.get('sale_price') if product_data.get('sale_price') > 1 else 2
        values['standard_price'] = product_data.get('cost_price')
        values['route_ids'] = self._prepare_route_values(product_data, supplier, is_produced)
        values['barcode'] = product_data.get('barcode')
        values['sale_ok'] = product_data.get('sold')
        values['purchase_ok'] = product_data.get('purchased')
        values['volume'] = product_data.get('volume', 0)
        values['weight'] = product_data.get('weight', 0)
        values['sale_delay'] = product_data.get('delivery_time', 0)
        values['product_brand_id'] = self.env['akustikken.product.brand'].search([('name', '=', product_data.get('brand'))], limit=1).id if product_data.get('brand') else False
        # Assign taxes for all companies and let record rules decide which to apply
        values['taxes_id'] = [(6, 0, [company.account_sale_tax_id.id for company in self.env['res.company'].sudo().search([])])]
        values['supplier_taxes_id'] = [(6, 0, [company.account_purchase_tax_id.id for company in self.env['res.company'].sudo().search([])])]
        values['created_by_trunk'] = True
        values['type'] = self.get_product_type(product_data)
        if product_data.get('sale_unit'):
            values['uom_id'] = self.env['uom.uom'].search([('name', 'ilike', product_data['sale_unit'])], limit=1).id
        if product_data.get('purchase_unit'):
            values['uom_po_id'] = self.env['uom.uom'].search([('name', 'ilike', product_data['purchase_unit'])], limit=1).id
        values['property_account_expense_id'] = False
        values['property_account_income_id'] = False
        return values

    def _prepare_route_values(self, product_data, supplier, is_produced, product=False):
        production_company = self.env['res.company'].search([('production', '=', True)])
        active_routes = []
        # Now we must define all standard routes for each company
        for company in self.env['res.company'].sudo().search([]):
            if company.production:
                routes = product.with_company(production_company).route_ids.mapped('code') if product else ["IN"] if is_produced or company.partner_id == supplier else ["SMTO", "ITO"] if supplier.is_mto else ["SMTO", "IN"]
                active_routes.extend(company.product_route_ids.sudo().filtered(lambda r: r.code in routes).ids)
            else:
                active_routes.extend(company.product_route_ids.sudo().filtered(lambda r: r.code in ["MTO", "DRS", "IN"]).ids)
        return [(6, 0, list(set(active_routes)))]

    def get_product_type(self, product_data):
        product_type = product_data.get('product_type') if product_data.get('product_type') else 'product'
        return product_type.lower()

    def is_production_product(self, product_data):
        """ Used to check if the product is produced by strai kjøkken. If so, it will be handled differently in the _handle_supplierinfo method
        :param list product_data : list of dictionaries containing product information
        :returns boolean
        """
        # Find out if the product category of the product from the trunk = the configured product category (or child categories)
        if product_data.get('product_category'):
            category = " / ".join(product_data['product_category'].split('/'))  # Add spaces around / from Trunk
            if category:
                category = self.env['product.category'].search([('complete_name', '=ilike', category)], limit=1)
                ir_config_parameter = self.env['ir.config_parameter'].sudo()
                default_category = ir_config_parameter.get_param('strai.production_product_category')
                if default_category == False:
                    raise UserError(_("A default production category is not set. Go to Settings(in applications) -> General Settings -> Trunk"))
                categories = self.env['product.category'].search([('id', 'child_of', int(default_category))])
                if category.id in categories.ids:
                    return True
        return False

    def is_production_company(self, supplier):
        """ Check if supplier is the production company
        :param object supplier
        :returns boolean
        """
        companies = self.env['res.company'].search([('production', '=', True)])
        if supplier.id in [c.partner_id.id for c in companies]:
            return True
        return False

    def _get_product_supplier(self, product_data):
        """ Get the supplier recordset that have a ref that matches the "supplier_code" from the product_data paramater
        :param object supplier
        :returns recordset : res.partner
        """
        if product_data.get('supplier_code'):
            partner_id = self.env['res.partner'].search([('ref', '=', product_data['supplier_code'])])
            if not partner_id:
                raise UserError(_('There are no partners that match the ref:{} from winner'.format(product_data['supplier_code'])))
            if len(partner_id) > 1:
                # There are more than one partner with the same ref
                raise UserError(_('There are more than one partner with the same ref: {}. All partner refs should be unique. Correct the refs and try again.'.format(product_data['supplier_ref'])))
            return partner_id
        else:
            partner_id = self.get_or_create_no_supplier_partner_ref()
        return partner_id

    def is_already_supplier(self, supplier, product, company, product_data):
        # Check if the product already has this supplier listed
        if supplier.ref == 'no_supplier' or not product_data.get('reference'):
            return False
        supplier_record = self.env['product.supplierinfo'].sudo().search([('company_id', '=', company.id), ('product_tmpl_id', '=', product.product_tmpl_id.id), ('winner_product_code', '=', product_data['reference']), ('partner_id', '=', supplier.id)])
        return any([supplier.id == existing.partner_id.id for existing in supplier_record])

    def unlink_other_suppliers(self, supplier, product, company, product_data):
        supplier_record = self.env['product.supplierinfo'].sudo().search([('company_id', '=', company.id), ('product_tmpl_id', '=', product.product_tmpl_id.id), ('winner_product_code', '=', product_data['reference']), ('partner_id', '!=', supplier.id)])
        supplier_record.unlink()

    def _handle_supplierinfo(self, product_data, product, supplier, is_produced, company):
        companies = self.env['res.company'].search([])
        production_company = companies.filtered(lambda c: c.production == True)
        # If the product is a manufacturing product, the production company is implicitly always the supplier
        if is_produced:
            # Create supplier info for all companies, except the supplier (Manufacturing company)
            if company.partner_id != supplier:
                # Don't create supplier info, if it already exists
                if not self.is_already_supplier(supplier, product, company, product_data):
                    self._create_supplierinfo(company, product, product_data, supplier)

        # If the product is supplied by 3rd party (Not produced), the production company is the supplier for all stores
        # And only the production company knows the real supplier, unless the 'direct_supplier' parameter is sent
        if not is_produced and company.partner_id != supplier:
            if company != production_company:
                # Create supplier for production company if it's not a direct supplier
                if not self.is_already_supplier(supplier, product, production_company, product_data) and not product_data.get('direct_supplier'):
                    self._create_supplierinfo(production_company, product, product_data, supplier)
                supplier = production_company.partner_id if not product_data.get('direct_supplier') else supplier
                # remove other suppliers, in case direct_supplier has changed since last time
                self.unlink_other_suppliers(supplier, product, company, product_data)
            if not self.is_already_supplier(supplier, product, company, product_data):
                self._create_supplierinfo(company, product, product_data, supplier)

    def _create_supplierinfo(self, company, product, product_data, supplier):
        if company.partner_id.id == supplier.id:
            return
        self.env['product.supplierinfo'].with_company(company).create({
            'partner_id': supplier.id,
            'price': product_data['sale_price'] if product_data['sale_price'] > 1 else 2,
            'product_code': product_data['reference'],
            'winner_product_code': product_data['reference'],
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'company_id': company.id,
            'delay': supplier.default_leadtime if supplier.default_leadtime else 14
        })

    def get_category_id(self, category_name):
        category_id = 0
        if category_name:
            if len(category_name) > 3:
                category_name = category_name.rsplit('/', 1)[1]
                capitalize_cat_name = category_name.capitalize()
                category_id = self.env['product.category'].search([('name', '=', capitalize_cat_name)], limit=1).id
            return category_id if category_id != 0 else self.env.ref('product.product_category_all').id
        else:
            return self.env.ref('product.product_category_all').id

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        context = self._context or {}
        if self._context.get('from_purchase_order', False):
            limit = 25
        return super(ProductProduct, self)._name_search(name, domain, operator, limit, order)