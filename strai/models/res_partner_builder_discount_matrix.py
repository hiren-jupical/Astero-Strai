from odoo import models, fields, api


class ResPartnerBuilderDiscountMatrix(models.Model):
    _name = 'res.partner.builder.discount.matrix'
    _description = 'Builder discount for each builder partner'

    partner_id = fields.Many2one('res.partner', string='Proff partner', required=True)
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
