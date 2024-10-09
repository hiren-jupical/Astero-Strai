# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    store_user_id = fields.Many2one('res.users', string='Store User')

    def action_send_so_to_store_email(self):
        self.ensure_one()
        template_id = self.env.ref('strai_email_so_to_store.email_template_for_so_to_store', raise_if_not_found=False)
        ctx = {
            'default_model': 'sale.order',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id if template_id else None,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
            'selger_category_partners': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
