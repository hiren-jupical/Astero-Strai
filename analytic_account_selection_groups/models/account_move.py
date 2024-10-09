from odoo import models, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        self.check_analytic_accounts()
        return super().action_post()

    def check_analytic_accounts(self):
        for move in self:
            valid = move.check_analytics()
            if not valid:
                move.raise_analytics_error()

    @api.model
    def check_analytics(self):
        valid = True
        # journal items, not invoice items. Should also block misc journals
        for line in self.line_ids:
            if line.account_id and line.account_id.analytic_account_mandatory and (not line.strai_analytic_account_id or not line.analytic_distribution):
                valid = False
                break
        return valid

    def raise_analytics_error(self):
        raise ValidationError(_('Mandatory field not set. Check analytic account'))
