#  -*- coding: utf-8 -*-
#  Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    confirmed_qty = fields.Float('Confirmed Qty.',digits='Product Unit of Measure', copy=False, readonly=True)
    sscc_number = fields.Char('SSCC No.', copy=False, readonly=True)
    status = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('exception', 'Exception'),
    ], string='Status.', copy=False, readonly=True)

    def _prepared_status_values(self, line_vals):
        confirmed_qty = line_vals.get('confirmed_qty')
        status = 'confirmed' if self.product_uom_qty == confirmed_qty else 'exception'
        return { 'status': status }
