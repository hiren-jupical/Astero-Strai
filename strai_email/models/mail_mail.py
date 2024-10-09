from odoo import models, api, fields, _
import json

class MailMail(models.Model):
    _inherit = 'mail.mail'

    #template_id = fields.Many2one('mail.template', string="Email Template", index=True,
                                  #help="Email template used to compose this message.")

    @api.model
    def create(self, values):
        # Determine custom reply-to email address based on model, resource ID, or template
        custom_reply_to = self._get_custom_reply_to(values)

        if custom_reply_to:
            # Ensure headers is a dictionary
            headers = values.get('headers', '')
            headers_dict = self._parse_headers(headers)
            headers_dict['Reply-To'] = custom_reply_to
            values['headers'] = self._format_headers(headers_dict)

        return super(MailMail, self).create(values)

    def _get_custom_reply_to(self, values):
        # Check if mail.template is used
        catchall_email = 'catchall@strai.no'

        # template_id = values.get('template_id')
        # if template_id:
        #     template = self.env['mail.template'].browse(template_id)
        #     if template and template.reply_to:
        #         return f'{template.reply_to};{catchall_email}'

        # Check model and resource ID
        model = values.get('model')
        res_id = values.get('res_id')

        if model and res_id:
            if model == 'sale.order':
                sale_order = self.env['sale.order'].browse(res_id)
                return f'{sale_order.user_id.email };{catchall_email}' if sale_order.user_id and not sale_order.is_production else catchall_email

            elif model == 'account.move':  # account.invoice is now account.move in newer Odoo versions
                account_move_record = self.env['account.move'].browse(res_id)
                if account_move_record and account_move_record.company_id.id == 7 and account_move_record.company_id.invoice_sender_email:  # designated logic for KRS
                    return f'{account_move_record.company_id.invoice_sender_email};{catchall_email}'
                elif account_move_record and account_move_record.move_type in ['out_invoice', 'out_refund'] and not \
                        account_move_record.company_id.production and not \
                        account_move_record.invoice_user_id.company_id.production:
                    return f'{account_move_record.invoice_user_id.partner_id.email};{catchall_email}'

            elif model == 'purchase.order':
                purchase_order = self.env['purchase.order'].search([('id', '=', res_id)], limit=1)
                if purchase_order and not purchase_order.is_production:
                    return f'{purchase_order.user_id.partner_id.email};{catchall_email}'
        return None

    def send(self, auto_commit=False, raise_exception=False):
        for mail in self:
            # Ensure headers is a dictionary
            headers = mail.headers or ''
            headers_dict = self._parse_headers(headers)

            custom_reply_to = self._get_custom_reply_to({
                'template_id': mail.template_id.id if hasattr(mail, 'template_id') else False,
                'model': mail.model,
                'res_id': mail.res_id,
            })

            if custom_reply_to:
                headers_dict['Reply-To'] = custom_reply_to
                mail.headers = self._format_headers(headers_dict)
                mail.reply_to = custom_reply_to

        return super(MailMail, self).send(auto_commit=auto_commit, raise_exception=raise_exception)

    def _parse_headers(self, headers):
        headers_dict = {}
        if headers:
            lines = headers.split('\n')
            for line in lines:
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    headers_dict[key] = value
        return headers_dict

    def _format_headers(self, headers_dict):
        headers = []
        for key, value in headers_dict.items():
            headers.append(f'{key}: {value}')
        return '\n'.join(headers)