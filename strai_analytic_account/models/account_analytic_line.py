from odoo import models, fields

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    strai_analytic_account_id_name = fields.Char(related="move_line_id.strai_analytic_account_id.name")