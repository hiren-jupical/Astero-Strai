# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict

from odoo import models
from odoo.tools.misc import groupby


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_invoice_lines_group_by_section(self):
        self.ensure_one()
        group_by_section = OrderedDict()
        section_name = 'Undefined'
        for line in self.invoice_line_ids.sorted(key=lambda l: (-l.sequence, l.date, l.move_name, -l.id), reverse=True):
            if line.display_type == 'line_section':
                section_name = line.id
                group_by_section[section_name] = []
            elif line.display_type != 'line_note':
                group_by_section[section_name] = group_by_section.get(section_name, []) + [line]
        data = []
        for section in group_by_section.keys():
            for tax in groupby(group_by_section[section], key=lambda l: l.tax_ids):
                tax_id = tax[0]
                line_ids = [line.id for line in tax[1]]
                groupby_tax = self.env['account.move.line'].read_group(
                    domain=[('id', 'in', line_ids)],
                    fields=['price_subtotal', 'price_total'], groupby=[])
                groupby_tax[0].update({
                    'tax_ids': ', '.join(tax_id.mapped('description')) if tax_id.description else '',
                    'section': self.invoice_line_ids.filtered(lambda il:il.id == section).name
                })
                data += groupby_tax
        return data
