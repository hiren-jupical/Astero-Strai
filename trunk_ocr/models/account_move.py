import base64
import json
import logging

import requests
from lxml import etree

from odoo import fields, models, api, _, Command
from odoo.exceptions import UserError
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

ENDPOINT = '/Document/ParseInvoice'


class AccountMove(models.Model):
    _inherit = "account.move"

    trunk_ocr_status = fields.Selection([
        ('ready', 'Ready'),
        ('processed', 'Processed'),
    ], default='ready')
    return_from_trunk = fields.Boolean(string="Return From Trunk")
    return_from_odoo_ocr = fields.Boolean(string="Return from Odoo OCR")
    odoo_ocr_result = fields.Text(string="Odoo OCR result")
    trunk_matched_purchase_orders = fields.Boolean(string="Trunk matched invoice against purchase orders", default=False)
    trunk_adjusted_invoice_lines = fields.Boolean(string="Trunk adjusted invoice lines", default=False)
    residual_amount = fields.Monetary()
    trunk_adjusted_currency = fields.Boolean(string="Trunk adjusted currency", default=False)

    def _cron_trunk_ocr(self, limit):
        moves = self.env['account.move'].search(['&', ('trunk_ocr_status', '=', 'ready'), '&', ('move_type', 'in', ['in_invoice', 'in_refund']), '&', ('state', '=', 'draft'), '|', ('return_from_odoo_ocr', '=', True), ('move_origin_type', 'in', ['ehf', 'intercompany'])], limit=limit)
        for move in moves:
            move.get_data_from_trunk(False)

    def get_data_from_trunk(self, raise_error=True):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        operation_mode_id = ir_config_parameter.get_param('strai.trunk_mode')
        operation_mode = self.env['trunk.endpoint'].search([('id', '=', operation_mode_id)])
        for move in self:
            # do not make adjustments to intercompany invoices
            if move.move_origin_type == 'intercompany':
                move.trunk_ocr_status = 'processed'
                continue

            if not move.partner_id.name or not move.ref:
                if raise_error:
                    raise UserError(_("Missing vendor or Invoice No"))
                else:
                    # avoid marking invoices processed too soon
                    continue

            # prev_move = self.env['account.move'].search([('partner_id', '=', move.partner_id.id), ('move_type', '=', 'in_invoice'), ('state', '=', 'posted'), ('len(ref)', '=', len(move.ref))], order='invoice_date desc', limit=1)
            # not able to match string length with standard search function
            query = """
                SELECT id 
                FROM account_move
                WHERE partner_id = %d 
                    AND move_type = 'in_invoice'
                    AND state = 'posted'
                    AND length(ref) = %s
                    AND company_id = %d
                ORDER BY invoice_date desc
                LIMIT 1 """ % (move.partner_id.id, len(move.ref), move.company_id.id)

            self.env.cr.execute(query)
            prev_move = self.env['account.move'].browse(self.env.cr.fetchone())

            # '' = new supplier, no info is found aboud previous payment references
            # '-1' = old supplier that should not have a payment reference
            # otherwise - send previous payment reference
            prev_payment_ref = ''
            if prev_move:
                prev_payment_ref = '-1'
                if prev_move.payment_reference:
                    prev_payment_ref = prev_move.payment_reference

            payload = {
                'invoiceno': move.ref,
                'prevKid': prev_payment_ref
            }

            files = []
            for i in move.attachment_ids.filtered(lambda x: x.mimetype == 'application/pdf'):
                file = ('file', (i.name, i.raw, 'application/pdf'))
                files.append(file)

            headers = {
                'ApiKey': ir_config_parameter.get_param('strai.trunk_password'),
                'ApiClient': ir_config_parameter.get_param('strai.trunk_username')
            }

            try:
                _logger.info("Running Trunk OCR on invoice %s from %s in company %s" % (move.ref, move.partner_id.name, move.company_id.name,))

                response = requests.request("POST", operation_mode.endpoint + ENDPOINT, headers=headers, data=payload, files=files)
                # move.message_post(body=_('Vendor bill has been sent to Trunk'))
                if response.ok:
                    content = json.loads(response.content)
                    move.message_post(body=_('Trunk Response') + '<br>' + response.text)
                    if move.move_origin_type == 'pdf':
                        payment_ref = content.get('kid')
                        acc_number = content.get('bank_account')
                        move._get_bank_account(acc_number)
                        move.payment_reference = payment_ref
                        move.adjust_currency()
                    purchase_orders = content.get('purchase_orders')
                    move.get_invoice_lines(purchase_orders)
                    move.adjust_invoice_lines()
                    move.adjust_information(purchase_orders)
                    move.adjust_products()
                    move.adjust_accounts()
                    move.return_from_trunk = True
                else:
                    _logger.error("Attachment scan failed %s" % (response.text,))
            except Exception as e:
                _logger.error("Attachment processing failed %s" % (e,))
            move.trunk_ocr_status = 'processed'

    @api.model
    def _get_bank_account(self, number):
        if not number:
            return
        bank = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.commercial_partner_id.id), ('acc_number', '=', str(number))])
        if not bank or len(bank) > 1:
            self.message_post(body=_("<strong style='color: red;'>Bank account not found %s</strong>") % number or "")
            return
        self.write({'partner_bank_id': bank.id})

    @api.model
    def get_invoice_lines(self, purchase_orders):
        orders = self.env['purchase.order'].search([('name', 'in', purchase_orders), ('company_id', '=', self.company_id.id), ('partner_id', '=', self.partner_id.id)])
        for order in orders:
            po_lines = order.order_line - self.line_ids.mapped('purchase_line_id')
            new_lines = self.env['account.move.line']
            for line in po_lines.filtered(lambda x: x.display_type not in ['line_section', 'line_note']):
                new_line = new_lines.new(line._prepare_account_move_line(self))
                # set correct qty, not just invoice qty. Ignore if the products are received
                new_line.quantity = line.product_qty
                # for some reason, when running automation the currency set is not used, and all values are converted to NOK
                new_line.price_unit = line.price_unit
                new_lines += new_line
            self.line_ids += new_lines
            self.partner_bank_id = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]
        if len(orders) > 0:
            self.trunk_matched_purchase_orders = True

    @api.model
    def adjust_invoice_lines(self):
        if self.trunk_matched_purchase_orders:
            total = self.get_total_amount()
            if not total or total == 0.0:
                # necessary information is not available
                _logger.debug('Could not read the XML file of EHF invoice')
                return

            # only correct the order lines if the total is found
            if total > 0.0:
                # find the order line that Odoo OCR has created with the total amount
                # did not work for EHF, as EHF is using the price before round off
                # total_order_line = self.invoice_line_ids.filtered(lambda l: l.display_type == 'product' and l.product_id.id is False and l.quantity == 1.0 and l.price_total == total and l.purchase_order_id.id is False)
                total_order_line = self.invoice_line_ids.filtered(lambda x: x.display_type == 'product' and x.product_id.id is False and x.quantity == 1.0 and x.purchase_order_id.id is False)
                # remove it
                if total_order_line:
                    total_order_line.unlink()
                # check if residual line exists before creating a new one
                residual_product = self.partner_id.residual_product if self.partner_id and self.partner_id.residual_product else self.env['product.product'].search([('default_code', '=', 'Prisavvik')], limit=1)
                existing_residual_line = self.invoice_line_ids.filtered(lambda x: x.product_id.id == residual_product.id)
                if existing_residual_line:
                    existing_residual_line.unlink()
                # remove any roundoffs before summing the lines
                ir_config_parameter = self.env['ir.config_parameter'].sudo()
                default_round_off_product = ir_config_parameter.get_param('strai.round_off_product')
                roundoff_product = self.env['product.product'].browse(int(default_round_off_product))
                existing_roundoff_line = self.invoice_line_ids.filtered(lambda x: x.product_id.id == roundoff_product.id)
                if existing_roundoff_line:
                    existing_roundoff_line.unlink()
                # calculate difference between PO lines and total
                total_pos = sum(self.invoice_line_ids.mapped('price_total'))
                # difference between total and total from PO's. Positive number if total is higher than PO, else negative
                self.residual_amount = total - total_pos

                if self.residual_amount != 0.0:
                    # get correct residual product
                    invoice_lines_from_pos = self.invoice_line_ids.filtered(lambda x: x.purchase_order_id is not False and x.display_type in ['product', False])
                    analytic_account = False
                    analytic_distribution = False
                    tax_ids = False
                    if len(invoice_lines_from_pos) > 0:
                        analytic_account = invoice_lines_from_pos[0].strai_analytic_account_id
                        analytic_distribution = invoice_lines_from_pos[0].analytic_distribution
                        tax_ids = invoice_lines_from_pos[0].tax_ids

                    self.invoice_line_ids = [Command.create({
                        'product_id': residual_product.id,
                        'name': residual_product.name,
                        'strai_analytic_account_id': analytic_account.id if analytic_account else False,
                        'analytic_distribution': analytic_distribution,
                        'quantity': 1.0,
                        # 'price_unit': self.residual_amount / (1 + tax_ids[0].amount / 100) if tax_ids and tax_ids[0].amount and tax_ids[0].amount > 0.0 and tax_ids[0].invoice_repartition_line_ids[1].factor_percent > 0.0 else self.residual_amount,
                        'price_unit': self.residual_amount / (1 + tax_ids[0].amount / 100) if tax_ids and tax_ids[0].amount and tax_ids[0].amount > 0.0 else self.residual_amount,
                        'tax_ids': tax_ids.ids,
                        'sequence': 10  # set residual product at top of order to make it visual to users
                    })]

                    self.roundoff(total)

                    self.message_post(body=_("Invoice lines adjusted to match total amount"))
                self.trunk_adjusted_invoice_lines = True

    @api.model
    def adjust_currency(self):
        if self.partner_id and self.partner_id.property_purchase_currency_id:
            self.currency_id = self.partner_id.property_purchase_currency_id
            self.trunk_adjusted_currency = True

    def adjust_information(self, purchase_orders):
        for move in self:
            purchase_order = self.env['purchase.order'].search([('name', '=', purchase_orders[0])]) if len(purchase_orders) > 0 else False
            if purchase_order:
                move.product_type_id = purchase_order.product_type_id
                move.order_type = purchase_order.order_type
                move.price_campaign_id = purchase_order.price_campaign_id
                move.sales_project_id = purchase_order.sales_project_id
                move.apartment_id = purchase_order.apartment_id
                move.builder_partner_id = purchase_order.builder_partner_id
                move.builder_agreement_situation = purchase_order.builder_agreement_situation
                move.store_name = purchase_order.store_name

    def adjust_products(self):
        for move in self:
            # check if a standard product is listed on the supplier. Apply this product on all lines if it exists
            if move.partner_id and move.partner_id.standard_product:
                # do not set product on line sections and line notes
                for line in move.invoice_line_ids.filtered(lambda y: y.display_type not in ['line_section', 'line_note'] and not y.purchase_line_id and not y.product_id):
                    # avoid price and name resets
                    price = line.price_unit
                    name = line.name
                    line.product_id = move.partner_id.standard_product.id
                    line.price_unit = price
                    line.name = name

    def adjust_accounts(self):
        for move in self:
            # check if a standard account is listed on the supplier. Apply this account on all lines if it exists
            if move.partner_id and move.partner_id.standard_account:
                for line in move.invoice_line_ids.filtered(lambda y: y.display_type not in ['line_section', 'line_note']):
                    line.account_id = move.partner_id.standard_account.id
                    line.tax_ids = move.partner_id.standard_account.tax_ids

    def roundoff(self, total):
        for move in self:
            # round off, not getting to accurate amount because of VAT
            roundoff = total - move.amount_total
            # do not enter a huge roundoff, this should only take away fractions. Otherwise, something else is wrong
            if round(roundoff, 2) != 0.00 and -0.1 <= roundoff <= 0.1:
                # get roundoff product
                ir_config_parameter = self.env['ir.config_parameter'].sudo()
                default_round_off_product = ir_config_parameter.get_param('strai.round_off_product')
                roundoff_product = self.env['product.product'].browse(int(default_round_off_product))
                if not default_round_off_product:
                    raise UserError(_("A default Roundoff Product is not set. Go to settings(In applications) --> General Settings --> Trunk"))

                # get roundoff line if it exists
                roundoff_line = move.invoice_line_ids.filtered(lambda x: x.product_id.id == roundoff_product.id)
                if roundoff_line:
                    # reset roundoff and recalculate the difference
                    roundoff_line.price_unit = 0.0
                    roundoff = total - move.amount_total
                    roundoff_line.price_unit = roundoff
                else:
                    move.invoice_line_ids = [Command.create({
                        'product_id': roundoff_product.id,
                        'name': roundoff_product.name,
                        'quantity': 1.0 if roundoff > 0.0 else -1.0,
                        'price_unit': abs(roundoff),
                        'sequence': 11  # set roundoff product above other order lines to make it visible, right under the price deviation line
                    })]

    @api.model
    def get_total_amount(self):
        total = 0.0
        # PDF
        if self.move_origin_type == 'pdf' and self.odoo_ocr_result:
            # use total amount (inc vat) from odoo OCR
            ocr_result = json.loads(self.odoo_ocr_result)
            # total = ocr_result['invoice_lines'][0]['total']['selected_value']['content'] if 'invoice_lines' in ocr_result and 'total' in ocr_result['invoice_lines'][0] else 0.0
            total = ocr_result['total']['selected_value']['content'] if 'total' in ocr_result else False
            if not total and 'invoice_lines' in ocr_result:
                # fall back to sum its lines
                total = 0
                for invoice_line in ocr_result['invoice_lines']:
                    if 'total' in invoice_line:
                        total += invoice_line['total']['selected_value']['content']
        elif self.move_origin_type == 'ehf':
            xml_file = self.attachment_ids.filtered(lambda x: x.name.endswith('.xml'))
            # EHF
            if xml_file:
                # use total amount (inc vat) from XML file
                # open XML
                xml_tree = etree.fromstring(base64.b64decode(xml_file.datas))
                payable_amount = xml_tree.xpath("/*[name()='Invoice']/*[name()='cac:LegalMonetaryTotal']/*[name()='cbc:PayableAmount']")
                if payable_amount:
                    total = float(payable_amount[0].text)
        elif self.auto_invoice_id:
            return self.amount_total
        return total

    # override function from account_invoice_extract to save information gathered from Odoo OCR service
    # a lot of information is coming from odoo OCR API, but for some reason it is not used properly
    # trying to leverage the information directly to avoid creating a custom OCR library containing everything Odoo does
    def _save_form(self, ocr_results, force_write=False):
        self.odoo_ocr_result = json.dumps(ocr_results, default=date_utils.json_default)
        self.return_from_odoo_ocr = True
        return super()._save_form(ocr_results, force_write=force_write)

    # override standard to avoid scanning intercompany invoices
    def _needs_auto_extract(self, new_document=False, file_type=''):
        """ Returns `True` if the document should not be intercompany invoice"""
        res = super()._needs_auto_extract(new_document=new_document, file_type=file_type)
        if res and self.filtered(lambda x: x.auto_invoice_id):
            return False
        return res
