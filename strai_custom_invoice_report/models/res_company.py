# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    flyt_inv_pdf_sections = fields.Boolean("Aggregate using sections in Invoice PDF")
