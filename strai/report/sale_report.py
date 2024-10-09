from odoo import models, fields, api, _


class SaleReport(models.Model):
    _inherit = 'sale.report'

    product_brand_id = fields.Many2one('akustikken.product.brand', readonly=True)
    product_series_id = fields.Many2one('akustikken.product.series', readonly=True)

    product_type_id = fields.Many2one('product.type', readonly=True, store=True)

    def _select_sale(self):
        select = super(SaleReport, self)._select_sale()
        select += """, 
            t.product_brand_id, 
            t.product_series_id,
            s.product_type_id,
            s.order_type"""
        return select

    def _group_by_sale(self):
        group_by = super(SaleReport, self)._group_by_sale()
        group_by += """, 
            t.product_brand_id, 
            t.product_series_id,
            s.product_type_id,
            s.order_type"""
        return group_by
