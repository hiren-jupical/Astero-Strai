from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # override standard function
    def _prepare_down_payment_section_line(self, **optional_values):
        down_payments_section_line = super()._prepare_down_payment_section_line(**optional_values)
        down_payments_section_line['name'] = 'Forskuddsbetaling'

        return down_payments_section_line
