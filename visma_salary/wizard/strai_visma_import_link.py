# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StraiVismaImportLink(models.TransientModel):
    _name = 'strai.visma.import.link'
    _description = 'strai.visma.import.link'

    report_file = fields.Binary(readonly=True)
    file_name = fields.Char()
