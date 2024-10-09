from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    analytic_line_id = fields.Many2one('account.analytic.line')
    original_unit_price = fields.Monetary()
