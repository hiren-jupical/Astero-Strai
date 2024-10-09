from odoo import fields, models, api, _


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'
    _order = ' partner_id desc,applied_on1, product_var_name, brand_and_series_ids'

    base = fields.Selection(
        selection_add=[
        ('purchase_price', 'Purchase Pricelist')],
        # ('store_purchase', 'Store Purchase Pricelist'),
        string="Based on",
        default='list_price', required=True,
        help='Base price for computation.\n'
             'Sales Price: The base price will be the Sales Price.\n'
             'Cost Price : The base price will be the cost price.\n'
             'Other Pricelist : Computation of the base price based on another Pricelist.',
        ondelete={'purchase_price': 'set default'})

    applied_on = fields.Selection(
        selection_add=[
        ('4_brands', 'Brands'),
        ('5_series', 'Series')],
        string="Apply On",
        default='3_global', required=True,
        ondelete={'4_brands': 'set default', '5_series': 'set default'},
        help='Pricelist Item applicable on selected option')

    applied_on1 = fields.Selection([
        ('0_global', 'All Products'),
        ('1_brands', 'Brands'),
        ('2_series', 'Series'),
        ('3_product', 'Product'),
        ('4_product_variant', 'Product Variant'),
        ('5_product_category', 'Product Category'), ], "Apply On1",
        compute="_set_applied_on_strai", store=True)

    product_var_name = fields.Char(string="Product var name", related='product_id.name', store=True)

    @api.depends('applied_on')
    def _set_applied_on_strai(self):
        for rec in self:
            if rec.applied_on == '3_global':
                rec.applied_on1 = '0_global'
            elif rec.applied_on == '1_product':
                rec.applied_on1 = '3_product'
            elif rec.applied_on == '0_product_variant':
                rec.applied_on1 = '4_product_variant'
            elif rec.applied_on == '2_product_category':
                rec.applied_on1 = '5_product_category'
            elif rec.applied_on == '4_brands':
                rec.applied_on1 = '1_brands'
            elif rec.applied_on == '5_series':
                rec.applied_on1 = '2_series'

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price', \
                 'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge')
    def _compute_name_and_price(self):
        res = super(ProductPricelistItem, self)._compute_name_and_price()
        for item in self:
            if item.brand_and_series_ids and item.applied_on == '4_brands':
                item.name = _("Brands: %s") % (item.brand_and_series_ids)
            elif item.series_id and item.applied_on == '5_series':
                item.name = _("Series: %s") % (item.series_id.display_name)
            elif item.product_id and item.applied_on == '0_product_variant':
                item.name = _("Variant: %s") % (item.product_id.with_context(display_default_code=False).display_name)

    brand_id = fields.Many2one('akustikken.product.brand')

    # Field for filtering available series
    brand_series_id = fields.Many2one('akustikken.product.brand')
    series_id = fields.Many2one('akustikken.product.series')
    partner_id = fields.Many2one("res.partner", compute='_get_main_supplier_strai', store=True)

    @api.depends('company_id', 'product_id', 'product_tmpl_id')
    def _get_main_supplier_strai(self):
        for rec in self:
            active_company_id = rec.pricelist_id.company_id and rec.pricelist_id.company_id.id or False
            partner_id = False
            if rec.applied_on == '0_product_variant' and rec.product_id and active_company_id:
                seller_ids = rec.product_id.seller_ids.filtered(lambda x: active_company_id == x.company_id.id)
                if seller_ids:
                    partner_id = seller_ids[0].partner_id and \
                                 seller_ids[0].partner_id.id or False

            elif rec.applied_on == '1_product' and rec.product_tmpl_id and active_company_id:
                seller_ids = rec.product_tmpl_id.seller_ids.filtered(lambda x: active_company_id == x.company_id.id)
                if seller_ids:
                    partner_id = seller_ids[0].partner_id and \
                                 seller_ids[0].partner_id.id or False

            rec.partner_id = partner_id

    @api.depends('brand_id', 'brand_series_id')
    def compute_brand_series(self):
        for record in self:
            record.brand_and_series_ids = record.brand_series_id.name if record.brand_series_id else record.brand_id.name if record.brand_id else False

    brand_and_series_ids = fields.Char(compute=compute_brand_series, store=True)

    # This method is not getting called from anywhere.
    # @api.depends('categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price',
    #              'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge', 'brand_id', 'series_id')
    # def _get_pricelist_item_name_price(self):
    #     for record in self:
    #         if record.brand_id:
    #             record.name = _("Brand: %s") % record.brand_id.name
    #         elif record.series_id:
    #             record.name = _("Series: %s") % record.series_id.name
    #         elif record.categ_id:
    #             record.name = _("Category: %s") % record.categ_id.name
    #         elif record.product_tmpl_id:
    #             record.name = record.product_tmpl_id.name
    #         elif record.product_id:
    #             record.name = record.product_id.display_name.replace('[%s]' % record.product_id.code, '')
    #         else:
    #             record.name = _("All Products")

    #         if record.compute_price == 'fixed':
    #             record.price = "%s %s" % (record.fixed_price, record.pricelist_id.currency_id.name)
    #         elif record.compute_price == 'percentage':
    #             record.price = _("%s %% discount") % record.percent_price
    #         else:
    #             record.price = _("%s %% discount and %s surcharge") % (record.price_discount, record.price_surcharge)

    @api.onchange('applied_on')
    def _onchange_applied_on(self):
        if self.applied_on != '0_product_variant':
            self.product_id = False
        if self.applied_on != '1_product':
            self.product_tmpl_id = False
        if self.applied_on != '2_product_category':
            self.categ_id = False
        if self.applied_on != '4_brands':
            self.brand_id = False
        if self.applied_on != '5_series':
            self.series_id = False
