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

import json
import logging
import werkzeug

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import consteq

from odoo.addons.microsoft_outlook.controllers.main import MicrosoftOutlookController

_logger = logging.getLogger(__name__)


class MicrosoftOutlookControllerExt(MicrosoftOutlookController):
    @http.route('/microsoft_outlook/confirm', type='http', auth='user')
    
    def microsoft_outlook_callback(self, code=None, state=None, error_description=None, **kwargs):
        """Callback URL during the OAuth process.

        Outlook redirects the user browser to this endpoint with the authorization code.
        We will fetch the refresh token and the access token thanks to this authorization
        code and save those values on the given mail server.
        """

        # Override hardcoded check
        # if not request.env.user.has_group('base.group_system'):
        #     _logger.error('Microsoft Outlook: Non system user try to link an Outlook account.')
        #     raise Forbidden()

        try:
            state = json.loads(state)
            model_name = state['model']
            rec_id = state['id']
            csrf_token = state['csrf_token']
        except Exception:
            _logger.error('Microsoft Outlook: Wrong state value %r.', state)
            raise Forbidden()

        if error_description:
            return request.render('microsoft_outlook.microsoft_outlook_oauth_error', {
                'error': error_description,
                'model_name': model_name,
                'rec_id': rec_id,
            })

        model = request.env[model_name]

        if not issubclass(type(model), request.env.registry['microsoft.outlook.mixin']):
            # The model must inherits from the "microsoft.outlook.mixin" mixin
            raise Forbidden()

        record = model.browse(rec_id).exists()
        if not record:
            raise Forbidden()

        if not csrf_token or not consteq(csrf_token, record._get_outlook_csrf_token()):
            _logger.error('Microsoft Outlook: Wrong CSRF token during Outlook authentication.')
            raise Forbidden()

        try:
            refresh_token, access_token, expiration = record._fetch_outlook_refresh_token(code)
        except UserError as e:
            return request.render('microsoft_outlook.microsoft_outlook_oauth_error', {
                'error': str(e.name),
                'model_name': model_name,
                'rec_id': rec_id,
            })

        # Add sudo to write
        record.write({
            'microsoft_outlook_refresh_token': refresh_token,
            'microsoft_outlook_access_token': access_token,
            'microsoft_outlook_access_token_expiration': expiration,
        })

        return request.redirect(f'/web?#id={rec_id}&model={model_name}&view_type=form')
