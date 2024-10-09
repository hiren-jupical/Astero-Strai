from odoo import models, fields


class AccountAccount(models.Model):

    _inherit = 'account.account'

    analytic_account_id = fields.Many2many('account.analytic.account', domain=[('account_analytic_type', '=', 'financial')],  string='Analytic Account')
    analytic_account_mandatory = fields.Boolean('Mandatory Analytic Account')
