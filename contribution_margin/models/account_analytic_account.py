from odoo import fields, models, api


class ContributionMarginUserData(models.Model):
    _name = 'contribution.margin.user.data'
    _description = 'Contribution Margin User Data'

    custom_credit = fields.Monetary(string='Salg')
    custom_debit = fields.Monetary(string='Kjøp')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency")
    custom_status = fields.Selection([
        ('checked', 'Checked'),
        ('not_checked', 'Not Checked'),
        ('checked_and_changed', 'Checked & Changed'),
    ], default='not_checked')
    comment = fields.Char(string='Comment')


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    contribution_data_ids = fields.One2many('contribution.margin.user.data', 'analytic_account_id',
                                            string='Contribution Margin Data')

    @api.depends('line_ids.amount')
    def _compute_debit_credit_balance(self):
        for rec in self:
            rec = rec.with_context(exclude_zero_line=True)
            super(AccountAnalyticAccount, rec)._compute_debit_credit_balance()
