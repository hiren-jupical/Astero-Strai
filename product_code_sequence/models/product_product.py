from odoo import models, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('default_code'):
                vals['default_code'] = self.env.ref('product_code_sequence.default_code_sequence')._next()
        return super(ProductProduct, self).create(vals_list)
