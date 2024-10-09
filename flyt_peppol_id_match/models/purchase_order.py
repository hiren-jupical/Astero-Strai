# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        purchase_order = super().button_confirm()
        for order in self:
            order.order_line._update_purchase_peppol_line_id()
        return purchase_order
