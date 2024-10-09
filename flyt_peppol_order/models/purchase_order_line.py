# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    confirmed_qty = fields.Float("Confirmed QTY", copy=False,)
    confirmed_price = fields.Float("Confirmed Price", copy=False,)
    line_status_code = fields.Selection(
        string="Line Status",
        selection=[('1', 'Added'), ('3', 'Changed'), ('5', 'Accepted'), ('7', 'Rejected'), ('42', 'Already Delivered')],
        copy=False
    )
    note = fields.Char("Note", copy=False, help="To indentified the reason for a new line added")
    price_qty_mismatch = fields.Boolean()
