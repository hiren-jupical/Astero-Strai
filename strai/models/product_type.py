from odoo import api, fields, models, _


class ProductType(models.Model):
    _name = 'product.type'
    _description = 'Product Type'
    _order = 'sequence, id'

    name = fields.Char('Product Type')
    product_type = fields.Selection([('product', 'Product')], string='Type', default='product', required=True)
    sequence = fields.Integer(help="Determine the display order", default=10)
