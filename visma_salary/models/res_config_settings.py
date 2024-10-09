# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def find_default_receivable(self):
        receiveable_account_id = self.env['account.account'].search([('id', '=', 531)])
        if not receiveable_account_id:
            return None
        else:
            return receiveable_account_id

    def find_default_payable(self):
        payable_account_id = self.env['account.account'].search([('id', '=', 623)])
        if not payable_account_id:
            return None
        else:
            return payable_account_id

    partner_payable_account = fields.Many2one('account.account', related='company_id.partner_payable_account', readonly=False)
    partner_receiveable_account = fields.Many2one('account.account', related='company_id.partner_receiveable_account', readonly=False)
