# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    flyt_pdf_append_ids = fields.Many2many('ir.attachment', string='Append Attachments')

    # def _inter_company_prepare_invoice_data(self, invoice_type):
    #     res = super(AccountMove, self)._inter_company_prepare_invoice_data(invoice_type)
    #     if invoice_type in ['in_invoice', 'in_refund']:
    #         # get original invoice and copy attachments
    #         res.update({'flyt_pdf_append_ids': []})
    #         orig_inv = self.env['account.move'].browse(res['auto_invoice_id'])
    #         for attachment in orig_inv.flyt_pdf_append_ids.filtered(lambda x: not x.name.lower().endswith('.xml')):
    #             att_obj = {
    #                 'name': attachment.name,
    #                 'type': 'binary',
    #                 'datas': attachment.datas,
    #                 'res_model': 'account.move'
    #             }
    #             res['flyt_pdf_append_ids'].append((0, 0, att_obj))
    #
    #     return res