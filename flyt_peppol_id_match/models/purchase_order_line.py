# -*- coding: utf-8 -*
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    peppol_line_id = fields.Integer('peppol_line_id', readonly=True, copy=False)

    def _update_purchase_peppol_line_id(self):
        peppol_line_ids = self.filtered(lambda line: line.display_type not in ('line_note', 'line_section') and not line.peppol_line_id)
        if not peppol_line_ids:
            return
        count = max(self.mapped('peppol_line_id')) or 0
        for line in peppol_line_ids:
            count += 1
            line.peppol_line_id = count
