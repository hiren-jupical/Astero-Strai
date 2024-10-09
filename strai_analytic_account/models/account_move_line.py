from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    strai_analytic_account_id = fields.Many2one('account.analytic.account', string='Analytisk', compute='analytic_distribution_changed', store=True, readonly=False)

    # Commented this because the analytic_distribution in the list and form has been updated by the Write method.
    @api.onchange('strai_analytic_account_id')
    def strai_analytic_account_id_changed(self):
        for move_line in self:
            if move_line.strai_analytic_account_id:
                move_line.analytic_distribution = {str(move_line.strai_analytic_account_id.id): 100}

    # will only trigger when manually changing the analytic distribution
    # this should not trigger recursive functions
    @api.depends('analytic_distribution')
    def analytic_distribution_changed(self):
        for move_line in self:
            # analytic_distribution is handled in another module (strai_exhibition_analytics) in this case
            if move_line.analytic_distribution:
                move_line.strai_analytic_account_id = int(list(move_line.analytic_distribution.keys())[0])
            else:
                move_line.strai_analytic_account_id = False

    def write(self, vals):
        res = super().write(vals)
        for move_line in self:
            if vals.get('strai_analytic_account_id') and move_line.strai_analytic_account_id:
                move_line.analytic_distribution = {str(move_line.strai_analytic_account_id.id): 100}
