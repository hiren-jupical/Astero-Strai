from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.constrains('default_code')
    def _check_default_code(self):
        for r in self:
            if r.default_code:
                prod = self.env['product.product'].search_count([('default_code', '=', r.default_code)])
                if prod > 1:
                    raise ValidationError(_(f'The internal reference already exists! {r.default_code}'))

