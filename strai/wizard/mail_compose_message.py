# -*- coding: utf-8 -*-
from odoo import fields, models, api


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        ctx = self.env.context
        attchment_ids = self.env['ir.attachment'].search([('is_drag_attachment', '=', True),('res_model', '=', ctx['default_model']), ('res_id', '=', ctx['default_res_ids'])])
        for wizard in self:
            if attchment_ids:
                new_attachment_ids = list(wizard.attachment_ids.ids)
                for attachment in attchment_ids:
                    new_attachment_ids.append(attachment.id)
                    attachment.write({'is_drag_attachment': False})
                wizard.write({'attachment_ids': [(6, 0, new_attachment_ids)]})
                return super(MailComposer, wizard)._action_send_mail(auto_commit=auto_commit)
            else:
                return super(MailComposer, wizard)._action_send_mail(auto_commit=auto_commit)

    def action_cancel(self):
        ctx = self.env.context
        attchment_ids = self.env['ir.attachment'].search([('is_drag_attachment', '=', True),('res_model', '=', ctx['default_model']), ('res_id', '=', ctx['default_res_ids'])])
        if attchment_ids:
            attchment_ids.unlink()
        return {'type': 'ir.actions.act_window_close'}
