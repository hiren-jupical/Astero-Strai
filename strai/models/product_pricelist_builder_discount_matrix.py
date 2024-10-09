from odoo import models, fields, api


class ProductPriceListBuilderDiscountMatrix(models.Model):
    _name = 'product.pricelist.builder.discount.matrix'
    _description = 'Pricelist discount matrix for builders'

    product_pricelist_id = fields.Many2one('product.pricelist', string='Prisliste', required=True)
    product_category_id = fields.Many2one('product.category', string='Product Category ID', required=False)
    product_brand_id = fields.Many2one('akustikken.product.brand', string='Brand', required=False)
    product_series_id = fields.Many2one('akustikken.product.series', string='Series', required=False, domain=[('product_brand_id', '=', product_brand_id)])
    agreement_discount = fields.Float(string='Avtalerabatt', required=False)
    customer_discount_option = fields.Float(string='Kunderabatt tilvalg', required=False, digits=(16, 2))
    customer_discount_referral = fields.Float(string='Kunderabatt henvisning', required=False, digits=(16, 2))
    commission_option = fields.Float(string='Provisjon tilvalg', required=False, digits=(16, 2))
    commission_referral = fields.Float(string='Provisjon henvisning', required=False, digits=(16, 2))

    product_category_name = fields.Char(string='Produktkategori', compute='_compute_product_category_name', store=False)

    @api.depends('product_category_id')
    def _compute_product_category_name(self):
        for record in self:
            record.product_category_name = record.product_category_id.name

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.update_partner_discount_matrix()
        return res

    def write(self, vals):
        res = super().write(vals)
        self.update_partner_discount_matrix()
        return res

    def unlink(self):
        pricelist_id = self.product_pricelist_id.id
        res = super().unlink()
        self.update_partner_discount_matrix(pricelist_id)
        return res

    # send pricelist_id as a variable in case of unlink, as the record does not exist when this function gets called
    def update_partner_discount_matrix(self, pricelist_id=False):
        for record in self:
            # TODO property_product_pricelist does not get called for some reason. Always looping through all builders
            partners = self.env['res.partner'].search([('is_builder', '=', True), ('property_product_pricelist', '=', pricelist_id or record.product_pricelist_id.id)])
            partners.compute_builder_discount_matrix()
