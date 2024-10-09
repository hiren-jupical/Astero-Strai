from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_procurement_values(self):
        self.ensure_one()
        res = super(StockMove, self)._prepare_procurement_values()
        if self.sale_line_id and self.sale_line_id.current_vendor:
            res['supplierinfo_id'] = self.sale_line_id.current_vendor
        return res
