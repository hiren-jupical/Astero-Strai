# -*- coding: utf-8 -*-
#Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.onchange('picked')
    def _onchange_picked(self):
        if self.picked:
            self.quantity = not self.quantity and self.product_uom_qty or self.quantity
        else:
            self.quantity = 0.0

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity, reserved_quant)
        if 'quantity' in vals and self.picking_id.picking_type_code == 'incoming': # Default zero can be for purchase receipts
            vals.update({'quantity': 0.0})
        return vals
