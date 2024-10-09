from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('default_code')
    def _check_default_code(self):
        for r in self:
            if r.default_code:
                prod = self.env['product.template'].search_count([('default_code', '=', r.default_code)])
                if prod > 1:
                    raise ValidationError(_('The internal reference already exists!'))
