from odoo import models, fields, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    account_analytic_type = fields.Selection([('standard', 'Standard'),
                                              ('financial', 'Financial'),
                                              ('exhibition', 'Exhibition'),
                                              ('project', 'Project')], default='standard')
