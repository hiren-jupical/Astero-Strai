
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    _sql_constraints = [
        (
            'id_is_unique_dummy',
            'unique(id)',
            'This is a dummy constraint'
        ),
        (
            'check_amount_not_negative',
            'unique(id)',
            'This is a dummy constraint'
        )
    ]

    def make_new_pay(self, payment_id):
        is_reconciled = payment_id.is_reconciled
        if is_reconciled:
            linez = [l.id for l in payment_id.move_id.line_ids]
            partials_credit = self.env['account.partial.reconcile'].search([('credit_move_id', 'in', linez)])
            partials_debit = self.env['account.partial.reconcile'].search([('debit_move_id', 'in', linez)])
            if not (partials_debit or partials_credit):
                raise ValidationError(_(f'Seems payment {payment_id.name} is not reconciled...'))
                
            invoice_id = partials_credit and partials_credit.debit_move_id or partials_debit.credit_move_id
            (partials_credit + partials_debit).unlink()

        payment_id.amount = -payment_id.amount
        new_type = (payment_id.payment_type == 'inbound') and 'outbound' or 'inbound'
        _logger.info(f'Payment {payment_id.id} snur type {payment_id.payment_type} til {new_type}')
        payment_id.payment_type = new_type

        if is_reconciled:
            #partial = self.env['account.partial.reconcile'].browse(partial)
            #lines = self.env['account.move.line'].browse(invoice_id)        
            lines = invoice_id.move_id.line_ids
            accs_invoice = set([x.account_id.id for x in lines])
            payment_lines = payment_id.move_id.line_ids.filtered(lambda line: line.account_id.id in accs_invoice and not line.reconciled)
            accs_payment = set([x.account_id.id for x in payment_lines])
            lines = lines.filtered(lambda line: line.account_id.id in accs_payment and not line.reconciled)
            #lines += self.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
            rec_lines = payment_lines + lines
            return rec_lines.reconcile()
        else:
            return None


    ###@api.model
    def turnaround(self, batch):
        _logger.info(_("All payments in the batch could share the same payment method."))                                
        bt = batch.batch_type
        for pay in batch.payment_ids:
            if pay.payment_type != bt:
                _logger.info(f"Snur inbound til outbond {pay.amount} {pay.amount_signed} {pay.payment_type}")
                newpay = self.make_new_pay(pay)
                #pay.amount = -pay.amount
                #pay.payment_type = 'outbound'
                _logger.info(f"Snudde inbound til outbond {pay.amount} {pay.amount_signed} {pay.payment_type}")

    @api.model
    def create_batch_payment(self):
        res = super(AccountPayment, self).create_batch_payment()
        batch_id = res['res_id']
        batch = self.env['account.batch.payment'].browse(batch_id)        
        _logger.info(f'create_batch_payment batch_id {batch_id} was created {batch.batch_type}')
        amts = [pay.amount_signed for pay in batch.payment_ids]
        amtname = [(pay.name, pay.amount_signed) for pay in batch.payment_ids]
        amtname_s = ' / '.join( [ '%s : %s' % (x[0], x[1]) for x in amtname ] )
        _logger.info('amountz (batch type %s) %s' % (batch.batch_type, amtname_s))
        
        batch.batch_type = (sum(amts) > 0) and 'inbound' or 'outbound'
        self.turnaround(batch)
        _logger.info(f'create_batch_payment sum is {sum(amts)} so type {batch.batch_type}')
        ###self.env['accounting.batch.payment'].write(batch)
        # Skal vi kalle write?
        return res