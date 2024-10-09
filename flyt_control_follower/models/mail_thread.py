# -*- coding: utf-8 -*-
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

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        """Compute recipients to notify based on subtype and followers. This
        method returns data structured as expected for ``_notify_recipients``."""
        recipient_data = super()._notify_get_recipients(message, msg_vals, **kwargs)
        if "notify_followers" in self.env.context and not self.env.context.get(
            "notify_followers", False
        ):
            # filter out all the followers
            pids = (
                msg_vals.get("partner_ids", [])
                if msg_vals
                else message.sudo().partner_ids.ids
            )
            recipient_data = [d for d in recipient_data if d["id"] in pids]
        return recipient_data
