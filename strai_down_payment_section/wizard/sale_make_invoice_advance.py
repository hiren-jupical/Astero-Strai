import time

from odoo import Command, models, _
from odoo.tools import float_is_zero


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, so_line):
        """ Override to add section to down payment in invoice only if the Down-payment option is selected. """
        invoice_vals = super()._prepare_invoice_values(order, so_line)
        if self.advance_payment_method == 'percentage' or self.advance_payment_method == 'fixed':
            invoice_vals['invoice_line_ids'].insert(0, Command.create(
                {'name': _('Down Payments'), 'display_type': 'line_section', 'sequence': 1}))
        return invoice_vals

    def _prepare_down_payment_section_values(self, order):
        so_values = super()._prepare_down_payment_section_values(order)
        so_values['name'] = _('Down Payments')
        return so_values

    def _get_down_payment_amount(self, order):
        self.ensure_one()
        if self.advance_payment_method == 'percentage':
            advance_product_taxes = self.product_id.taxes_id.filtered(lambda tax: tax.company_id == order.company_id)
            if all(order.fiscal_position_id.map_tax(advance_product_taxes).mapped('price_include')):
                amount = order.amount_total * self.amount / 100
            else:
                amount = order.amount_untaxed * self.amount / 100
        else:  # Fixed amount
            amount = self.fixed_amount
        return amount

    def _prepare_down_payment_lines_values(self, order):
        self.ensure_one()
        analytic_distribution = {}
        amount_total = sum(order.order_line.mapped("price_total"))
        if not float_is_zero(amount_total, precision_rounding=self.currency_id.rounding):
            for line in order.order_line:
                distrib_dict = line.analytic_distribution or {}
                for account, distribution in distrib_dict.items():
                    analytic_distribution[account] = distribution * line.price_total + analytic_distribution.get(account, 0)
            for account, distribution_amount in analytic_distribution.items():
                analytic_distribution[account] = distribution_amount/amount_total
        so_values = {
            'name': _('Down Payment: %s (Draft)', time.strftime('%m %Y')),
            'price_unit': self._get_down_payment_amount(order),
            'product_uom_qty': 0.0,
            'order_id': order.id,
            'discount': 0.0,
            'product_id': self.product_id.id,
            'analytic_distribution': analytic_distribution,
            'is_downpayment': True,
            'sequence': order.order_line and order.order_line[-1].sequence + 1 or 10,
        }
        return so_values
