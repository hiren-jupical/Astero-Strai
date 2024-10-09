# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.osv import expression


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'


    partner_ids = fields.Many2many(domain="partner_ids_domain")
    partner_ids_domain = fields.Binary(compute='_compute_partner_ids_domain')

    @api.depends('subject')
    def _compute_partner_ids_domain(self):
        if self.env.context.get('selger_category_partners', False):
            tag_domain = [('category_id.f_store_email_recipient_domain', '=', True)]
        else:
            tag_domain = []
        for compose in self:
            compose.partner_ids_domain = tag_domain