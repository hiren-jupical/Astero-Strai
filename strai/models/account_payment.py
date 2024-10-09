from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    invoice_refs = fields.Text(compute='_compute_invoice_refs', readonly=True, store=True)

    @api.depends('reconciled_bill_ids')
    def _compute_invoice_refs(self):
        for payment in self:
            if payment.reconciled_bill_ids and len(payment.reconciled_bill_ids) > 0:
                payment.invoice_refs = ', '.join([inv.ref for inv in payment.reconciled_bill_ids if inv.ref]) or False
