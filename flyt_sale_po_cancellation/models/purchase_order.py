from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_sale_orders(self):
        res = super(PurchaseOrder, self)._get_sale_orders()
        res |= self.env['sale.order'].search([('name', 'ilike', self.origin)])
        return res
