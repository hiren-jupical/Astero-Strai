from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vendor_stock_level = fields.Float(related='product_id.product_tmpl_id.vendor_stock_level', readonly=True, store=False)
    vendor_stock_control = fields.Boolean(related='product_id.product_tmpl_id.vendor_stock_control', readonly=True, store=False)
