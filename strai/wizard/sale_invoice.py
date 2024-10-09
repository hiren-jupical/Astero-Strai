from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    # Field and function used to compute match between ordered and delivered quantities on a Sales order.
    qty_match = fields.Boolean(compute='_check_qty')

    @api.depends('amount')
    def _check_qty(self):
        self.qty_match = True
        so = self.env['sale.order'].browse(self._context.get('active_ids', []))
        
        for line in so.order_line:
            if line.product_uom_qty != line.qty_delivered:
                self.qty_match = False

    def create_invoices(self):
        self._check_amount_is_positive()
        invoices = self._create_invoices(self.sale_order_ids)
        if self.env.context.get('open_invoices'):
            return self.sale_order_ids.action_view_invoice(invoices=invoices)
        return {'type': 'ir.actions.act_window_close'}
