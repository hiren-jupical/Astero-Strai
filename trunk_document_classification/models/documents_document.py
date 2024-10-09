from datetime import datetime

import requests
import json

from odoo import models, fields

from ..helper.workarea_enum import WorkAreaEnum


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'

    classification_status = fields.Selection([
        ('new', 'New'),
        ('processed', 'Processed'),
        ('failed', 'Failed')
    ], default='new')
    classification_result = fields.Selection([
        ('invoice', 'Invoice'),
        ('creditnote', 'Creditnote'),
        ('noattachment', 'No attachment'),
        ('unknown', 'Unknown')
    ], required=False)
    classification_timestamp = fields.Datetime()

    def _cron_classify_documents(self, limit):
        documents = self.env['documents.document'].search([('classification_status', '=', 'new')], limit=limit)
        documents.classify_documents()

    def classify_documents(self):
        for document in self:
            # TODO if no attachments, no classification needed

            files = [
                ('file', (document.attachment_name, document.raw, 'application/pdf'))
            ]

            document.classification_timestamp = datetime.now()
            response = requests.request('POST', self._get_base_endpoint() + '/Document/ClassifyDocument', headers=self._get_default_headers(), files=files)

            if response and response.status_code == 200:
                result = json.loads(response.content)
                document.classification_result = result['classificationResult']
                if document.classification_result == 'invoice':
                    document.folder_id = WorkAreaEnum.FinanceInvoices
                elif document.classification_result == 'creditnote':
                    document.folder_id = WorkAreaEnum.FinanceCreditnotes
                elif document.classification_result in ['noattachment', 'unknown']:
                    document.folder_id = WorkAreaEnum.FinanceUnknown
                document.classification_status = 'processed'
            else:
                document.classification_result = 'failed'

    # trunk communication
    def _get_base_endpoint(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        operation_mode_id = ir_config_parameter.get_param('strai.trunk_mode')
        trunk_endpoint = self.env['trunk.endpoint'].search([('id', '=', operation_mode_id)])
        return trunk_endpoint.endpoint

    def _get_default_headers(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        headers = {
            'ApiKey': ir_config_parameter.get_param('strai.trunk_password'),
            'ApiClient': ir_config_parameter.get_param('strai.trunk_username'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return headers
