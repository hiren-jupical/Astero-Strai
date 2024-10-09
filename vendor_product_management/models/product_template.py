from odoo import models, fields, api
from ..helper.product_route_enum import RouteEnum


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_stock_control = fields.Boolean(default=False, help='Indicates if this products stock is controlled and updated by vendor. If checked, the product will be checked for available stock before it could be sold or purchased.')
    vendor_stock_level = fields.Float(compute="_compute_vendor_stock_level")
    deprecated = fields.Boolean(compute='_compute_deprecated')

    @api.depends('seller_ids.stock_level')
    def _compute_vendor_stock_level(self):
        production_company = self._get_production_company()
        for product in self:
            # use the first vendor for simplicity
            prod_seller_ids = product.seller_ids.sudo().filtered(lambda x: x.company_id == production_company)
            if prod_seller_ids and len(prod_seller_ids) > 0:
                product.vendor_stock_level = prod_seller_ids[0].stock_level
            else:
                product.vendor_stock_level = False

    @api.depends('seller_ids.deprecated')
    def _compute_deprecated(self):
        production_company = self._get_production_company()
        for product in self:
            # use the first vendor for simplicity
            prod_seller_ids = product.seller_ids.sudo().filtered(lambda x: x.company_id == production_company)
            if prod_seller_ids and len(prod_seller_ids) > 0:
                product.deprecated = prod_seller_ids[0].deprecated
            else:
                product.deprecated = False

    def update_vendor_products(self, data):
        production_company = self.env['res.company'].search([('production', '=', True)])
        currency_nok = self.env['res.currency'].search([('name', '=', 'NOK')])
        for vendor_product in data['vendor_products']:
            product = self._get_or_create_product(production_company.id, vendor_product)
            self._update_weight_volume_barcode_vendor_stock_control(product, vendor_product)
            self._update_or_create_supplierinfo(production_company.id, currency_nok.id, product, vendor_product)

        self._deprecate_products(data['vendor_products'])

    def _get_or_create_product(self, company_id, vendor_product):
        product = self._get_product(company_id, vendor_product)
        if not product:
            product = self._create_product(vendor_product)

        return product

    def _get_product(self, company_id, vendor_product):
        # get existing product if it exists
        # get by vendor product code, and if not exist, get by Winner code
        # if that does not exist either, try to use default code
        supplierinfo = self.env['product.supplierinfo'].search([
            ('partner_id', '=', vendor_product['PartnerId']),
            '|',
            ('product_code', '=', vendor_product['ProductCode']),
            ('winner_product_code', '=', vendor_product['Winnercode']),
            ('company_id', '=', company_id)
        ], limit=1)

        if supplierinfo:
            product = self.env['product.product'].search([
                '&',
                ('product_tmpl_id', '=', supplierinfo.product_tmpl_id.id),
                ('active', 'in', [True, False]),
            ], limit=1)

            return product

        # not found
        return False

    def _create_product(self, vendor_product):
        # create product
        product = self.env['product.product'].create({
            # Description contains Winnercode at the start, but sometimes it is empty
            'name': vendor_product['Description'] if vendor_product['Description'] else vendor_product['Winnercode'],
            'detailed_type': 'product',
            'default_code': vendor_product['ProductCode'],
            'company_id': False,
            'sale_ok': True,
            'purchase_ok': True,
            'route_ids': [RouteEnum.Buy.value, RouteEnum.BuyMto.value, RouteEnum.RefillOnOrder.value],
            'product_tag_ids': False
        })

        # set product category, brand and series
        product_category = self.env['product.category'].search([('name', '=', vendor_product['ProductCategory'])])
        brand = self.env['akustikken.product.brand'].search([('name', '=', vendor_product['Brand'])])
        series = self.env['akustikken.product.series'].search([('product_brand_id', '=', brand.id), ('name', '=', vendor_product['Series'])])
        product.product_tmpl_id.write({
            'categ_id': product_category.id,
            'product_brand_id': brand.id,
            'product_series_id': series.id
        })

        return product

    @staticmethod
    def _update_weight_volume_barcode_vendor_stock_control(product, vendor_product):
        product.product_tmpl_id.write({
            'weight': vendor_product['Weight'],
            'volume': vendor_product['Volume'],
            'barcode': vendor_product['ProductCode'],
            'vendor_stock_control': True
        })

    def _update_or_create_supplierinfo(self, company_id, currency_id, product, vendor_product):
        # get supplierinfo
        supplierinfo = self._get_supplierinfo(company_id, product, vendor_product)
        if not supplierinfo:
            supplierinfo = self._create_supplierinfo(company_id, currency_id, product, vendor_product)

        # update info
        supplierinfo.write({
            'price': vendor_product['PurchasePrice'],
            'product_code': vendor_product['ProductCode'],
            'stock_level': vendor_product['StockLevel'],
            'deprecated': False
        })

    @staticmethod
    def _get_supplierinfo(company_id, product, vendor_product):
        # supplierinfo = self.env['product.supplierinfo'].search([('company_id', '=', company_id), ('partner_id', '=', vendor_product['PartnerId']), ('winner_product_code', '=', vendor_product['WinnerCode'])])
        supplierinfo = product.product_tmpl_id.seller_ids.filtered(lambda x: x.partner_id.id == vendor_product['PartnerId'] and x.company_id.id == company_id and x.winner_product_code == vendor_product['Winnercode'])
        return supplierinfo

    def _create_supplierinfo(self, company_id, currency_id, product, vendor_product):
        # create supplierinfo
        supplierinfo = self.env['product.supplierinfo'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'partner_id': vendor_product['PartnerId'],
            'company_id': company_id,
            'price': vendor_product['PurchasePrice'],
            'currency_id': currency_id,
            'product_code': vendor_product['ProductCode'],
            'product_name': vendor_product['Winnercode'],
            'winner_product_code': vendor_product['Winnercode'],
        })

        return supplierinfo

    def _deprecate_products(self, vendor_products):
        # same partner for all vendor products for each batch
        partner_id = vendor_products[0]['PartnerId']
        product_codes = [product['ProductCode'] for product in vendor_products] + ['DIV', 'Miljøgebyr']
        supplierinfos = self.env['product.supplierinfo'].search([('partner_id', '=', partner_id), ('product_code', 'not in', product_codes), ('deprecated', '=', False), ('product_tmpl_id.detailed_type', '=', 'product')])
        supplierinfos.write({'deprecated': True})

    def _get_production_company(self):
        production_company = self.env['res.company'].search([('production', '=', True)])
        return production_company
