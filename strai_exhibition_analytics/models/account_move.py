from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_order_id = fields.Many2one('sale.order')

    def action_post(self):
        for move in self:
            if move.move_type == 'out_invoice':
                for line in move.invoice_line_ids:
                    if line.analytic_line_id:
                        # Standard odoo will take product cost price and insert into analytic account unit amount onchange quantity (amount). 
                        # We want the cost price from the PO, so we save the
                        # original unit price in a field on the line to use on this move and to kredit the customer account.
                        if not line.original_unit_price:
                            line.original_unit_price = line.analytic_line_id.amount/(line.analytic_line_id.unit_amount or 1)
                        lines_vals = {'unit_amount': line.analytic_line_id.unit_amount - line.quantity,
                                        'amount': line.original_unit_price*line.analytic_line_id.unit_amount}
                        line.analytic_line_id.sudo().update(lines_vals)


                        if line.analytic_distribution:
                            vals={}
                            vals.update({'name': line.name,
                                        'amount': line.original_unit_price * line.quantity,
                                        'unit_amount': line.quantity,
                                        'product_id': line.product_id.id,
                                        'product_uom_id': line.product_uom_id.id,
                                        'account_id': int(list(line.analytic_distribution.keys())[0])})
                            self.env['account.analytic.line'].sudo().create(vals)
        return super(AccountMove, self).action_post()
