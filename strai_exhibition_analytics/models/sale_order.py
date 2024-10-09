from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = "sale.order"

    def action_analytic_products(self):
        """Open wizard that contains analytic_account_lines"""
        wizard = self.env['analytic.exhibition.lines'].create({
            'order_id': self.id,
            'analytic_account_lines_ids': [(0,0, {
                'name': line.name,
                'unit_amount': line.unit_amount,
                'product_id': line.product_id.id,
                'analytic_line_id': line.id,
                'invoice_id': line.move_line_id.move_id.id
            }) for line in self.exhibit_analytic_account_id.exhibit_analytic_line_ids]
        })
        return {
            'name': _('Exhibition Products'),
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'analytic.exhibition.lines',
            'res_id': wizard.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.onchange('order_type')
    def onchange_order_type(self):
        if not self.order_type == 'exhibit':
            self.exhibit_analytic_account_id = False

    def action_confirm(self):
        """ Adds functionality to standard odoo funtion.
            IF order_type is exhibit and it's in a store, change route on all order lines to Make To Order"""
        for order in self:
            if order.order_type == 'exhibit' and not order.is_production and not order.sale_to_self:
                delivery_route_id = self.env['stock.route'].search([('code', '=', 'DEL')])
                for line in order.order_line:
                    line.route_id = delivery_route_id.id
        return super(SaleOrder, self).action_confirm()

    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)
            for move in invoices:
                move.sale_order_id = order.id if order.id and isinstance(order.id, int) else False
