from odoo import models, api

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        self.ensure_one()
        if not self.composition_mode == 'mass_mail' and self.template_id:
            self = self.with_context(default_template_id=self.template_id.id)
        return super(MailComposeMessage, self).action_send_mail()

    def _prepare_mail_values(self, res_ids):
        mail_values = super(MailComposeMessage, self)._prepare_mail_values(res_ids)
        template_id = self._context.get('default_template_id')
        if template_id:
            mail_values['template_id'] = template_id
        return mail_values