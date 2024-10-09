from odoo import models, fields


class ProductBrand(models.Model):
    _name = 'akustikken.product.brand'
    _description = 'Products brands'

    name = fields.Char("Name", translate=True)
    product_series_ids = fields.One2many("akustikken.product.series", 'product_brand_id', string="Series")
