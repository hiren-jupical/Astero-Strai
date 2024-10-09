# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields


class MailWizardInvite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    def add_followers(self):
        if self.res_model in ['sale.order', 'purchase.order']:
            return super(MailWizardInvite, self.with_context(from_add_followers=True)).add_followers()
        return super().add_followers()
