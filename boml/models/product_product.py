from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    checksum = fields.Char("Checksum")
