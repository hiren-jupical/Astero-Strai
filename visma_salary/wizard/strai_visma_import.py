# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import base64
import csv
import io

_logger = logging.getLogger(__name__)


class StraiVismaImport(models.TransientModel):
    _name = 'strai.visma.import'
    _description = 'strai.visma.import'

    date_from = fields.Date()
    date_to = fields.Date()

    def action_generate_import_csv(self):
    
        lines = self.get_open_partner_ledger_lines()
        report_file = base64.b64encode(self._generate_csv(lines))

        file_link = self.env['strai.visma.import.link'].create({'file_name': 'Strai-Visma-report.csv', 'report_file': report_file})
        return {
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'strai.visma.import.link',
            'res_id': file_link.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def get_open_partner_ledger_lines(self):
        lines = self._create_query()
        return lines

    def _create_query(self):
        partner_payable_account = self.env.company.partner_payable_account
        partner_receiveable_account = self.env.company.partner_receiveable_account
        if partner_payable_account is False or partner_receiveable_account is False:
            raise UserError(_("Payable and receivable accounts are not found. Go to configuration(in applications) --> Accounting --> Visma Export"))

        company_id = self.env.company
        journals = self.env['account.journal'].search([('company_id', '=', company_id.id)]).ids

        partner_ids = self.env['hr.employee'].search([('work_contact_id', '!=', False)])
        private_partner_ids = []
        for partner in partner_ids:
            private_partner_ids.append(partner.work_contact_id.id)

        date_from = self.date_from
        date_to = self.date_to

        strai_accounts = partner_payable_account.id, partner_receiveable_account.id
        
        query = ''' 
                SELECT account_move_line.partner_id,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)) AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)) AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance
                FROM account_move_line
                INNER JOIN account_move AS move ON move.id = account_move_line.move_id
                LEFT JOIN (VALUES (%d, 1.0, 2)) AS currency_table(company_id, rate, precision)
                    ON currency_table.company_id = account_move_line.company_id
                WHERE (account_move_line.display_type NOT IN ('line_section', 'line_note') OR account_move_line.display_type IS NULL)
                AND account_move_line.date <= '%s'
                AND account_move_line.date >= '%s'
                AND account_move_line.partner_id IN %s
                AND move.state = 'posted'
                AND (account_move_line.credit != 0.0
                    OR account_move_line.debit != 0.0
                    OR (account_move_line.amount_currency = 0.0
                        OR account_move_line.journal_id IN %s))
                AND account_move_line.account_id IN %s
                AND (account_move_line.company_id IS NULL OR account_move_line.company_id = %d)
                GROUP BY account_move_line.partner_id
                ''' % (company_id.id, date_to.strftime('%Y-%m-%d'), date_from.strftime('%Y-%m-%d'), tuple(private_partner_ids), tuple(journals), strai_accounts, company_id.id)

        self._cr.execute(query)
        result = self._cr.dictfetchall()
        return self._get_lines(result)

    @api.model
    def _get_lines(self, lines):
        _logger.info(lines)
        lines_list = {}
        for line in lines:
            lines_list[line['partner_id']] = {'lønnsår': 0,
                                              'kjørenummer': 0,
                                              'ansattnummer': self.find_partner_ref(line['partner_id']),
                                              'lønsart': 805,
                                              'grunnlag': 0,
                                              'antall': 0,
                                              'sats': 0,
                                              'beløb': line['balance'],
                                              'kontonummer': 0,
                                              'motkonto': 0,
                                              'avdeling': '""',
                                              'projekt': '""',
                                              'ekstra1': '""',
                                              'ekstra2': '""',
                                              'ekstra3': '""',
                                              'kampanje': '""',
                                              'trekkode': 0}
        _logger.info(lines_list)
        return lines_list

    def _generate_csv(self, lines):
        csv_file = io.StringIO()
        csv_writer = csv.writer(csv_file, delimiter=';', quotechar=',', quoting=csv.QUOTE_NONE)
        for key in lines:
            csv_writer.writerow([lines[key]['lønnsår'],
                                 lines[key]['kjørenummer'],
                                 lines[key]['ansattnummer'],
                                 lines[key]['lønsart'],
                                 lines[key]['grunnlag'],
                                 lines[key]['antall'],
                                 lines[key]['sats'],
                                 lines[key]['beløb'],
                                 lines[key]['kontonummer'],
                                 lines[key]['motkonto'],
                                 lines[key]['avdeling'],
                                 lines[key]['projekt'],
                                 lines[key]['ekstra1'],
                                 lines[key]['ekstra2'],
                                 lines[key]['ekstra3'],
                                 lines[key]['kampanje'],
                                 lines[key]['trekkode']])

        return csv_file.getvalue().encode('latin1')

    def find_partner_ref(self, partner):
        partner_id = self.env['res.partner'].search([('id', '=', partner)])
        return partner_id.ref
