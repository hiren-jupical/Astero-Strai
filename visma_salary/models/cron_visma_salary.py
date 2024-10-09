import logging
import base64
from odoo.exceptions import UserError
from odoo import models, _

_logger = logging.getLogger(__name__)


class CronVismaSalary(models.TransientModel):
    _name = 'cron.visma.salary'
    _description = 'cron.visma.salary'

    def _cron_visma_salary(self):
        for company in self.env['res.company'].search([]):
            self._company_cron_visma_salary(company)

    def _company_cron_visma_salary(self, company):
        lines = []
        files = self.env['ir.attachment'].sudo().search([('integration_system', '=', 'VismaSalary'), ('integration_status', '=', 'new'), ('company_id', '=', company.id)])
        for file in files:
            try:
                string_file = base64.decodebytes(file.datas).decode('utf-8')
                for x in string_file.split('\r'):
                    if any(char.isdigit() for char in x):
                        lines.append(x)
                move = self.create_account_move(lines, company)
                # move.action_post()
                file.integration_status = 'processed'
            except Exception:
                file.integration_status = 'failed'
                raise

    def create_account_move(self, lines, company):
        account_move = self.with_company(company)._create_account_move(company)
        account_move.line_ids = self.line_values(account_move, lines, company)
        return account_move

    def _create_account_move(self, company):
        company_id = company
        journal = self.env['account.journal'].search([('code', '=', 'LONN'), ('company_id', '=', company_id.id)])
        if not journal:
            raise UserError(_("There isn't any journal with code 'LONN' for company %s.") % (company_id.name))
        account_move = self.env['account.move'].create({'state': 'draft',
                                                        'ref': 'Visma',
                                                        'journal_id': journal.id,
                                                        'currency_id': company_id.currency_id.id,
                                                        })
        return account_move

    def line_values(self, account_move, lines, company):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        company_id = company
        values = []
        account_id = False
        account_config_id = False
        for line in lines:
            account_number = self.process_account_number(line, company)
            if account_number == False:
                continue
            amount = self.get_amount(line)
            is_debit = self.is_debit(line)
            partner = None
            if account_number.get('partner_id'):
                partner = account_number.get('partner_id').id
                account_config_id = self.env.company.partner_receiveable_account
            else:
                account_id = account_number.get("account_number")
            if is_debit == True:
                debit = amount
                # credit = None
                values.append((0, 0, {'move_id': account_move.id,
                                      'currency_id': company_id.currency_id.id,
                                      'partner_id': partner,
                                      'account_id': self.find_account(account_id,
                                                                      company).id if account_id else account_config_id.id,
                                      'debit': debit}))
            else:
                # debit = None
                credit = amount
                values.append((0, 0, {'move_id': account_move.id,
                                      'currency_id': company_id.currency_id.id,
                                      'partner_id': partner,
                                      'account_id': self.find_account(account_id,
                                                                      company).id if account_id else account_config_id.id,
                                      'credit': credit
                                      }))
        return values

    def find_account(self, account_id, company):
        account = self.env['account.account'].search([('code', '=', account_id), ('company_id', '=', company.id)], limit=1)
        if not account:
            raise UserError(_(f" There is no account with code: {account_id} in {company.name}"))
        return account

    def is_debit(self, line):
        symbol = line[83]
        if symbol == '0':
            symbol = line[84]
        if symbol == '-':
            return False
        else:
            return True

    # Find partner id from account number. If not a partner, return the account number for use as account.
    def process_account_number(self, line, company):
        account_number = line[1:9]
        try:
            int_account_number = int(account_number)
        except:
            int_account_number = False
        if type(int_account_number) == False:
            return False
        original_account_number = account_number
        partner_id = self.env['res.partner'].search(
            [('ref', '=', original_account_number.lstrip('0')), ('company_id', '=', company.id)], limit=1)
        if not partner_id:
            stripped_account_number = account_number.lstrip('0')
            # If account number is bigger than 100000. It belongs to a partner, but there is no partner with the ref. Raise error.
            if int(stripped_account_number) > 100000:
                _logger.info(f'! COULD NOT IMPORT VISMA DATA. THERE IS NO PARTNER WITH REF: {original_account_number}')
                raise UserError(
                    f'! COULD NOT IMPORT VISMA DATA. THERE IS NO PARTNER WITH REF: {original_account_number}')
            else:
                return {'account_number': stripped_account_number[0:4]}
        else:
            return {'partner_id': partner_id}

    def get_amount(self, line):
        amount = line[85:95]
        amount.lstrip('0')
        float_amount = float(amount.lstrip('0')) / 100
        return float_amount
