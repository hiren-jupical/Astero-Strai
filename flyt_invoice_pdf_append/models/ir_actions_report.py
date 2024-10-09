# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import models
from odoo.tools import pdf


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if self._get_report(report_ref).report_name in ('account.report_invoice_with_payments'):
            invoices = self.env['account.move'].browse(res_ids)
            merged_pdf = []
            for invoice in invoices.filtered(lambda i: i.move_type in ('out_invoice', 'out_refund')):
                merged_pdf.append(super()._render_qweb_pdf(report_ref, res_ids=invoice.id, data=data)[0])
                for attachment in invoice.flyt_pdf_append_ids.filtered(lambda a: a.mimetype.endswith('pdf')):
                    datas = base64.b64decode(attachment.datas)
                    merged_pdf += [datas]
            pdf_merged = pdf.merge_pdf(merged_pdf)
            return pdf_merged, 'pdf'
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
