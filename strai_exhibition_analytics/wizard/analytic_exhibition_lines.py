from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class AnalyticExhibitionLines(models.TransientModel):
    _name = 'analytic.exhibition.lines'
    _description = 'Analytic Exhibition Lines'

    @api.model
    def _get_default_order(self):
        return self._context.get('active_id')

    order_id = fields.Many2one('sale.order', default=_get_default_order)
    analytic_account_lines_ids = fields.Many2many('analytic.exhibition.line.missing')

    def add_analytic_account_line(self):
        for line in self.analytic_account_lines_ids:
            if line.chosen_amount:
                if line.chosen_amount > 0 and not line.chosen_amount > line.unit_amount:
                    vals = {'product_id': line.product_id.id,
                            'order_id': self.order_id.id,
                            'name': line.name,
                            'product_uom_qty': line.chosen_amount,
                            'analytic_line_id': line.analytic_line_id.id,
                            'from_analytic_account': True
                            }
                    self.env['sale.order.line'].create(vals)
                else:
                    raise UserError(_("You didn't choose an amount or the amount you choose were bigger than the available amount"))
