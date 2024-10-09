from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    from_analytic_account = fields.Boolean(default=False, required=False)
    analytic_line_id = fields.Many2one('account.analytic.line')

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({'analytic_line_id': self.analytic_line_id.id})
        return res
