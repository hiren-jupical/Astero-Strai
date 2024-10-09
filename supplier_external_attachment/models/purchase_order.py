import requests
import base64

from odoo import models, api, _
from odoo.exceptions import UserError


class MailTemplate(models.Model):
    _inherit = 'purchase.order'

    def _process_attachments_for_template_post(self, mail_template):
        """ Add attachments to templates. """
        # Call super to generate the basic email values
        result = super()._process_attachments_for_template_post(mail_template)
        # Iterate over each record_id for which the email is being generated
        for po in self:
            if po.partner_id and po.partner_id.attach_e01_purchase and po.origin and (po.origin.startswith(prefix) for prefix in ('SF', 'SB')):
                # get related sale order
                so = self.env['sale.order'].search([('name', '=', po.origin)], limit=1)
                if not so or not so.winner_file_id or so.winner_file_id == '1':
                    continue
                po_result = result.setdefault(po.id, {})
                e01file, filename = self._get_e01_file_from_trunk(so.winner_file_id)
                if not e01file or not filename:
                    continue

                # converts file into a base64 encoded file (byte list), and then converted to a string (b64 string using utf-8)
                b64_e01file = base64.b64encode(e01file).decode('utf-8')

                # Attach the .e01 files to the email
                po_result.setdefault('attachments', []).append((filename, b64_e01file))
        return result

    def _get_e01_file_from_trunk(self, winnerfile_id):
        endpoint = '/Winner/GetE01File'

        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        operation_mode_id = ir_config_parameter.get_param('strai.trunk_mode')
        operation_mode = self.env['trunk.endpoint'].search([('id', '=', operation_mode_id)])
        payload = {
            'winnerfileId': int(winnerfile_id)
        }

        api_client = ir_config_parameter.get_param('strai.trunk_username')
        api_key = ir_config_parameter.get_param('strai.trunk_password')
        if isinstance(api_client, str) and isinstance(api_key, str):
            headers = {
                'ApiKey': api_key,
                'ApiClient': api_client
            }
        else:
            raise UserError('ApiClient and ApiKey must be strings.')

        response = requests.request("GET", operation_mode.endpoint + endpoint, headers=headers, data=payload)
        if response.status_code == 200:
            e01file = response.content
            filename = response.headers.get('Content-Disposition', '').split('filename*=UTF-8\'\'')[-1].split('filename=')[-1].strip('";\'')
            return e01file, filename
        else:
            raise UserError(_('Not able to fetch E01 file from Trunk. Try again'))
