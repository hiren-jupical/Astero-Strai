from odoo import models, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    edi_comment = fields.Char()
    edi_status = fields.Selection(related='order_id.edi_status', readonly=True)
