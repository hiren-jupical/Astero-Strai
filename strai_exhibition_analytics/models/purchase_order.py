from odoo import models, api, fields, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = "purchase.order"

    exhibit_analytic_account_id = fields.Many2one('account.analytic.account')

    @api.onchange('order_type')
    def onchange_order_type(self):
        if not self.order_type == 'exhibit':
            self.exhibit_analytic_account_id = False

    @api.onchange('exhibit_analytic_account_id')
    def onchange_exhibit_account(self):
        if self.exhibit_analytic_account_id:
            for line in self.order_line:
                line.analytic_distribution = {str(self.exhibit_analytic_account_id): 100}
