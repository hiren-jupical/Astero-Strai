from odoo import fields, models, api


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    exhibit_analytic_line_ids = fields.One2many(
        'account.analytic.line',
        string="Analytic Lines",
        compute='_compute_exhibit_analytic_line_ids'
    )

    @api.depends()
    def _compute_exhibit_analytic_line_ids(self):
        self.exhibit_analytic_line_ids = False
        for plan, accounts in self.grouped('plan_id').items():
            domain = [('company_id', 'in', [False] + self.env.companies.ids)]
            line_groups = self.env['account.analytic.line']._read_group(
                domain=domain + [(plan._column_name(), 'in', self.ids)],
                groupby=[plan._column_name(), 'id'],
            )
        for account, line in line_groups:
            self.exhibit_analytic_line_ids += line
