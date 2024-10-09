from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    make_required_analytic_account_id = fields.Boolean('Make Required Analytic Account')
    analytic_account_id = fields.Many2many('account.analytic.account', compute = "_compute_analytic_account_id")

    @api.onchange('account_id')
    def _onchange_account_id(self):
        res = {}
        if self.move_id.move_type == 'in_invoice' or self.move_id.move_type == 'in_refund':
            if self.account_id:
                self.make_required_analytic_account_id = False
                # if self.account_id.analytic_account_id.ids:
                #     res = {'domain': {'strai_analytic_account_id': [('id', 'in', list(self.account_id.analytic_account_id.ids))]}}
                if self.account_id.analytic_account_mandatory:
                    self.make_required_analytic_account_id = True
                if res:
                    return res

    def _compute_analytic_account_id(self):
        for line in self:
            line.analytic_account_id = line.account_id.analytic_account_id.ids if line.account_id and line.account_id.analytic_account_id.ids and \
                line.move_id.move_type in ['in_invoice', 'in_refund'] else self.env['account.analytic.account'].search([]).ids
            if line.account_id.analytic_account_mandatory:
                line.make_required_analytic_account_id = True
   