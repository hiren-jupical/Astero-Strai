from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, so_line):
        vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, so_line)
        vals.update({
            'product_type_id': order.product_type_id.id,
            'order_type': order.order_type,
            'remarks': order.remarks,
        })
        return vals
