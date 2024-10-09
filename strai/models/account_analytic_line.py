from odoo import models, fields


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    account_analytic_type = fields.Selection(related='account_id.account_analytic_type')
    # [('standard', 'Standard'),
    #  ('financial', 'Financial'),
    #  ('exhibition', 'Exhibition'),
    #  ('project', 'Project')]
    return_from = fields.Char(string="Retur fra")
    return_date = fields.Date(string="Returdato")
    note = fields.Html(string="Notat")

    expected_sales_price = fields.Monetary(string="Forventet salgspris inkl. mva.")

    # override the string of amount
    amount = fields.Monetary(string="Innkjøpspris")
