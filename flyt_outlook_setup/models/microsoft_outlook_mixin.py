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

from odoo import api, models, fields, _

class MicrosoftOutlookMixinExt(models.AbstractModel):

    _inherit = 'microsoft.outlook.mixin'
    
    microsoft_outlook_refresh_token = fields.Char(groups='base.group_user')
    microsoft_outlook_access_token = fields.Char(groups='base.group_user')
    microsoft_outlook_access_token_expiration = fields.Integer(groups='base.group_user')

#   Override function in its entirety to remove the hardcoded check on admin rights
    def open_microsoft_outlook_uri(self):
        """Open the URL to accept the Outlook permission.

        This is done with an action, so we can force the user the save the form.
        We need him to save the form so the current mail server record exist in DB and
        we can include the record ID in the URL.
        """
        self.ensure_one()

        # if not self.env.user.has_group('base.group_system'):
        #     raise AccessError(_('Only the administrator can link an Outlook mail server.'))

        if not self.is_microsoft_outlook_configured:
            raise UserError(_('Please configure your Outlook credentials.'))

        return {
            'type': 'ir.actions.act_url',
            'url': self.microsoft_outlook_uri,
        }

