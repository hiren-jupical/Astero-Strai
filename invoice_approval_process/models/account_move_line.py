from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    approved_manager_user_id = fields.Many2one('res.users', string='Approved Manager', related='move_id.approved_manager_user_id', store=True)
