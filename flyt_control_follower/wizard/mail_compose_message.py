##############################################################################
#
#    Flyt Consulting AS
#    Copyright (C) 2018-TODAY Flyt Consulting AS(<http://www.flytconsulting.no>).
#    Author: Flyt Consulting AS(<http://www.flytconsulting.no>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    notify_followers = fields.Boolean(default=False)

    def _action_send_mail(self, auto_commit=False):
        result_mails_su, result_messages = (
            self.env["mail.mail"].sudo(),
            self.env["mail.message"],
        )
        for wizard in self:
            wizard = wizard.with_context(notify_followers=wizard.notify_followers)
            res_mail, res_message = super(MailComposeMessage, wizard)._action_send_mail(
                auto_commit=auto_commit
            )
            result_mails_su += res_mail
            result_messages += res_message
        return result_mails_su, result_messages

class AccountMoveSend(models.TransientModel):

    _inherit = "account.move.send"

    notify_followers = fields.Boolean(default=False)
