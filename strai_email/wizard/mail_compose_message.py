# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from ast import literal_eval


class MailComposerStrai(models.TransientModel):
    _inherit = "mail.compose.message"

    is_important = fields.Boolean("High Importance")

    def _action_send_mail(self, auto_commit=False):
        res = super()._action_send_mail(auto_commit=False)

        if self.is_important:
            headers_dic = literal_eval(res[1].mail_ids.headers)

            headers_dic["X-Priority"] = "1"
            headers_dic["X-MSMail-Priority"] = "High"
            headers_dic["Importance"] = "High"

            updated_headers_str = str(headers_dic)

            res[1].mail_ids.write({"headers": updated_headers_str})

        return res
