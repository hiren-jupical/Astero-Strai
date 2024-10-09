""" Enable creation of batch payments from both invoices and credit notes"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError



_logger = logging.getLogger(__name__)
_logger.error('GJEDNA!!!!')

class AccountBatchPayment(models.Model):    
    _inherit = 'account.batch.payment'

    @api.constrains('batch_type', 'journal_id', 'payment_ids')
    def _check_payments_constrains(self):
        for record in self:                        
            _logger.error('GJEDNA!!!!')
            all_companies = set(record.payment_ids.mapped('company_id'))
            if len(all_companies) > 1:
                raise ValidationError(_("All payments in the batch must belong to the same company."))
            all_journals = set(record.payment_ids.mapped('journal_id'))
            if len(all_journals) > 1 or (record.payment_ids and record.payment_ids[:1].journal_id != record.journal_id):
                raise ValidationError(_("The journal of the batch payment and of the payments it contains must be the same."))
            all_types = set(record.payment_ids.mapped('payment_type'))
            if all_types and record.batch_type not in all_types:
                raise ValidationError(_("The batch must have the same type as the payments it contains."))
            all_payment_methods = record.payment_ids.payment_method_id            
            if len(all_payment_methods) > 1:
                _logger.info(_("All payments in the batch could share the same payment method."))                                
                #bt = record.batch_type
                #for pay in record.payment_ids:
                #    if pay.payment_type != bt:
                #        _logger.info(f"Snur inbound til outbond {pay.amount} {pay.amount_signed} {pay.payment_type}")
                #        newpay = self.make_new_pay(pay)
                #        #pay.amount = -pay.amount
                #        #pay.payment_type = 'outbound'
                #        _logger.info(f"Snudde inbound til outbond {pay.amount} {pay.amount_signed} {pay.payment_type}")
                #raise ValidationError(_("All payments in the batch must share the same payment method."))
            # Since we accept positive payments now
            amounts = [pay.amount_signed for pay in record.payment_ids ]
            amtname = [(pay.name, pay.amount_signed) for pay in record.payment_ids]
            amtname_s = ' / '.join( [ '%s : %s' % (x[0], x[1]) for x in amtname ] )
            _logger.info('amountz (batch type %s) %s' % (record.batch_type, amtname_s))

            #if record.batch_type == 'inbound' and sum(amounts) > 0:
            #    raise ValidationError(_("KANSKJE The sum of amounts would be positive, amount of payments must be greater than amount of refunds."))
            #if record.batch_type == 'outbound' and sum(amounts) < 0:
            #    raise ValidationError(_("GJEDNA The sum of amounts would be negative, amount of payments must be greater than amount of refunds."))
            if all_payment_methods and record.payment_method_id not in all_payment_methods:
                raise ValidationError(_("The batch must have the same payment method as the payments it contains."))
            payment_null = record.payment_ids.filtered(lambda p: p.amount == 0)
            if payment_null:
                raise ValidationError(_('You cannot add payments with zero amount in a Batch Payment.'))
            non_posted = record.payment_ids.filtered(lambda p: p.state != 'posted')
            if non_posted:
                raise ValidationError(_('You cannot add payments that are not posted.'))
            
    def gurba_make_new_pay(self, payment_id):
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


"""

    def js_assign_outstanding_line(self, line_id):
        ''' Called by the 'payment' widget to reconcile a suggested journal item to the present
        invoice.

        :param line_id: The id of the line to reconcile with the current invoice.
        '''
        self.ensure_one()
        lines = self.env['account.move.line'].browse(line_id)
        lines += self.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
        return lines.reconcile()

        

    def js_remove_outstanding_partial(self, partial_id):
        ''' Called by the 'payment' widget to remove a reconciled entry to the present invoice.

        :param partial_id: The id of an existing partial reconciled with the current invoice.
        '''
        self.ensure_one()
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        return partial.unlink()

"""
