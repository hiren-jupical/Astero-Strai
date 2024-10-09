from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    production_product_category = fields.Many2one('product.category', config_parameter='strai.production_product_category')
    round_off_product = fields.Many2one('product.product', config_parameter='strai.round_off_product')

    # default_capacity_booking_product_category = fields.Many2one('product.category', default_model='sale.order')
    capacity_booking_product_category = fields.Many2one('product.category', config_parameter='strai.capacity_booking_product_category')
    warranty_product_id = fields.Many2one('product.product', related='company_id.warranty_product_id', string="Reklamasjonsprodukt", readonly=False)
    pass_through_billing_product_id  = fields.Many2one('product.product', related='company_id.pass_through_billing_product_id', string="Viderefaktureringsprodukt", readonly=False)

    # builder settings
    builder_special_pricelist = fields.Many2one('product.pricelist', string='Spesial prisliste', config_parameter='strai.builder_special_pricelist')
