# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Since path will be the same for each company, here has to be inserted a default data path. Made this way to avoid hardcoding.
    partner_payable_account = fields.Many2one('account.account')
    partner_receiveable_account = fields.Many2one('account.account')

    @api.model
    def _find_company_from_partner(self, partner_id):
        company = self.sudo().search([('partner_id', '=', partner_id)],
                                     limit=1)
        return company or False
