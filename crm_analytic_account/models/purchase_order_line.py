from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def create(self, vals):
        res = super(PurchaseOrderLine, self).create(vals)
        origin = res.order_id.origin
        sale_order = self.env['sale.order'].search([('name', '=', origin)])
        if sale_order:
            for line in res:
                line.analytic_distribution = {str(sale_order.analytic_account_id.id): 100}
        return res
