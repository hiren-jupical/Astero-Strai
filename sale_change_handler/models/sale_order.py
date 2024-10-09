from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # cancel all PO's when sale order is cancelled
    # activities for PO's is generated in Odoo standard
    def action_cancel(self):
        for so in self:
            if not so.sale_to_self:
                pos = self.env['purchase.order'].search([('origin', '=', so.name), ('state', 'in', ['draft'])])
                for po in pos:
                    po.button_cancel()
        return super().action_cancel()
