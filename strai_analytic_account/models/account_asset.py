from odoo import models, fields, api


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    strai_analytic_account_id = fields.Many2one('account.analytic.account')

    @api.onchange('strai_analytic_account_id')
    def onchange_analytic_account(self):
        for asset in self:
            if asset.strai_analytic_account_id:
                asset.analytic_distribution = {str(asset.strai_analytic_account_id.id): 100}
