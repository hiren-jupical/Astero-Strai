# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    flyt_gross_total = fields.Float(string="gross total", compute='_compute_flyt_gross_total', store=True)

    @api.depends('order_line.price_total')
    def _compute_flyt_gross_total(self):
        for order in self:
            gross_total = sum([line.price_unit * line.product_uom_qty for line in order.order_line])
            order.flyt_gross_total = gross_total

    def _compute_tax_totals(self):
        for order in self:
            res = super()._compute_tax_totals()
            tax_total = order.tax_totals
            tax_total.update({'gross_total_name': _('Bruttosum'),
                              'formatted_gross_total': formatLang(self.env, order.flyt_gross_total, currency_obj=order.currency_id)})
            order.tax_totals = tax_total
