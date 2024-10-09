# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models


class AccountReport(models.Model):
    _inherit = "account.report"

    def _get_lines(self, options, all_column_groups_expression_totals=None, warnings=None):
        """ Get the value when report opens for the first. """
        lines = super()._get_lines(options=options,
                                   all_column_groups_expression_totals=all_column_groups_expression_totals,
                                   warnings=warnings)
        for line in lines:
            value_diff = self._get_difference(line, options)
            line['value_diff'] = value_diff

        return lines

    def _format_column_values(self, options, line_dict_list, force_format=False):
        """ Need to adjust the value based on the change in the column. """
        for line_dict in line_dict_list:
            value_diff = self._get_difference(line_dict, options)
            line_dict['value_diff'] = value_diff
        super(AccountReport, self)._format_column_values(options=options, line_dict_list=line_dict_list,
                                                         force_format=force_format)

    def _get_difference(self, line_dict, options):
        """ get difference from the newly updated values """
        value_diff = 0
        if line_dict['columns'] and len(line_dict['columns']) == 2:
            col1 = line_dict['columns'][0]
            col2 = line_dict['columns'][1]
            if col1 and col2:
                no_format_val_1 = col1.get('no_format', False)
                no_format_val_2 = col2.get('no_format', False)
                if no_format_val_1 and no_format_val_2:
                    value_diff = self.format_value(options, (no_format_val_1 - no_format_val_2),
                                                   currency=col1.get('currency'),
                                                   blank_if_zero=col1.get('blank_if_zero'),
                                                   figure_type=col1.get('figure_type'), digits=col1.get('digits'))
        return value_diff
