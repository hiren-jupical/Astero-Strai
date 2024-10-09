from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_purchase_orders(self):
        res = super(SaleOrder, self)._get_purchase_orders()
        res |= self.env['purchase.order'].search([('origin', 'ilike', self.name), ('company_id', '=', self.company_id.id)])
        return res
