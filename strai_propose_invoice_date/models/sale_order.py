# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        '''INHERIT THIS FUNCTION TO ADD INVOICE_DATE AS PER THE LATEST DATE OF DELIVERY'''
        vals = super(SaleOrder, self)._prepare_invoice()
        if vals['move_type'] == 'out_invoice':
            done_pickings = self.picking_ids.filtered(lambda l: l.state == 'done')
            if done_pickings:
                invoice_date = done_pickings.mapped('date_done')
                vals.update({
                    'invoice_date': max(invoice_date)
                })
        return vals
