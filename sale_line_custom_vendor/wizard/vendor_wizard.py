# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models


_logger=logging.getLogger(__name__)


class VendorWizard(models.TransientModel):
    _name = 'vendor.wizard'

    sale_order_line = fields.Many2one('sale.order.line')
    current_vendor = fields.Many2one('product.supplierinfo', related='sale_order_line.current_vendor', readonly=True)
    vendor_ids = fields.Many2many('product.supplierinfo', compute="_compute_product_related_vendor_ids")
    vendors_selection = fields.Many2one('product.supplierinfo', domain="[('id', 'in', vendor_ids)]")

    def _compute_product_related_vendor_ids(self):
        for wizard in self:
            wizard.vendor_ids = wizard.sale_order_line.product_id.with_company(self.sale_order_line.company_id).seller_ids

    def save(self):
        sale_line_id = self.env['sale.order.line'].search([('id', '=', self._context.get('active_id'))])
        sale_line_id.alternative_vendor = self.vendors_selection
        _logger.info(f'SAVED VENDOR {sale_line_id.alternative_vendor}')
        return
