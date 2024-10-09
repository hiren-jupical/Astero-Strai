from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    auto_approval_status = fields.Selection([
        ('new', 'New'),
        ('supplier_not_enabled', 'Supplier Not Enabled'),
        ('invalid', 'Invalid'),  # required fields are not set and invoice needs to be controlled and adjusted manually
        ('validated', 'Validated'),
        ('products_not_received', 'Products Not Received'),
        ('not_approved', 'Not approved'),  # unable to auto approve this invoice. Must be approved manually
        ('approved', 'Approved')
    ], default='new', string='Auto approve status', required=False)
    auto_approved_timestamp = fields.Datetime()
    auto_approval_info = fields.Text()
    auto_post_status = fields.Selection([
        ('new', 'New'),
        ('not_enabled', 'Not enabled'),
        ('not_auto_posted', 'Not auto posted'),
        ('auto_posted', 'Auto posted'),
    ], default='new', string='Auto post status', required=False)

    def _cron_auto_approve_invoices(self, limit=500):
        # get invoices ready to be approved
        # all procedures should have runned before attempting auto approval
        invoices = self.env['account.move'].search(
            ['|', ('trunk_ocr_status', '=', 'processed'), ('auto_invoice_id', '!=', False),
             ('move_type', 'in', ['in_invoice', 'in_refund']), ('invoice_approver_calculated', '=', True),
             ('approved_manager_user_id', '=', False),
             ('auto_approval_status', 'in', ['new', 'products_not_received'])], limit=limit)
        invoices.auto_approve_invoice()

    def auto_approve_invoice(self):
        self.validate_for_auto_approval()
        for move in self:
            # validate invoice
            # this also validates that all lines are connected to purchase orders,
            # and that all products are received
            move.validate_for_auto_approval()
            if move.auto_approval_status == 'validated':
                # check if total amount in invoice matches total amount from OCR/EHF. No residual allowed here, as this is the payable amount
                total = move.get_total_amount()
                if round(total, 2) != round(move.amount_total, 2):
                    move.set_auto_approval_status('not_approved', ['Total amount from OCR/EHF/intercompany do not match total entered on invoice'])
                    continue

                # check that total amount is allowed for auto approval
                if 0 < move.partner_id.auto_approval_max_amount < move.amount_total:
                    move.set_auto_approval_status('not_approved', ['Max amount exceeded'])
                    continue

                if move.partner_id.auto_approval_require_received_products:
                    # check for received products
                    # do not check sections or notes
                    # do not check roundoff- and residual products, as these will never be connected to PO's
                    residual_product = move.get_residual_product()
                    roundoff_product = move.get_roundoff_product()
                    products_received = all(
                        line.product_id and line.purchase_line_id and line.purchase_line_id.qty_received == line.quantity
                        for line in move.invoice_line_ids
                        .filtered(lambda x: x.display_type in ['product', False] and x.product_id.id not in [
                            roundoff_product.id, residual_product.id]))

                    if not products_received:
                        move.set_auto_approval_status('products_not_received', ['Products not received'])
                        continue

                # approve intercompany invoices
                if move.auto_invoice_id:
                    move.auto_approve_intercompany_invoice()
                # approve OCR and EHF invoices
                elif move.trunk_ocr_status == 'processed':
                    move.auto_approve_pdf_ehf_invoice()
                if move.auto_approval_status == 'approved':
                    move.auto_post_invoice()

    def auto_approve_pdf_ehf_invoice(self):
        for move in self:
            residual_product = move.get_residual_product()
            roundoff_product = move.get_roundoff_product()

            # apply settings for residuals on head level, taking residual product and roundoff products into account
            total_residual = sum(line.price_total for line in move.invoice_line_ids.filtered(
                lambda x: x.product_id.id in [residual_product.id, roundoff_product.id]))

            # check that the total residual is below the threshold entered on the supplier
            if abs(total_residual) <= move.partner_id.auto_approval_max_residual_total:
                move.set_auto_approval_status('approved')
            else:
                move.set_auto_approval_status('not_approved', ['Too high residual amount'])

    def auto_approve_intercompany_invoice(self):
        for move in self:
            # get source PO
            purchase_orders = {line.purchase_order_id for line in move.invoice_line_ids if line.purchase_order_id}
            if not purchase_orders or len(purchase_orders) != 1:
                move.set_auto_approval_status('not_approved', ['Unclear which purchase order that belongs to this invoice'])
                continue
            purchase_order = list(purchase_orders)[0]

            # compare total value against total value of invoice, allow residual set to supplier
            residual = purchase_order.amount_total - move.amount_total
            if abs(residual) <= move.partner_id.auto_approval_max_residual_total:
                move.set_auto_approval_status('approved')
            else:
                move.set_auto_approval_status('not_approved', ['Too high residual amount'])

    def auto_post_invoice(self):
        for move in self:
            if not move.partner_id.auto_approval_auto_post:
                move.set_auto_post_status('not_enabled')
                continue

            move.action_post()
            move.set_auto_post_status('auto_posted')

    def validate_for_auto_approval(self):
        for move in self:
            if not move.partner_id.auto_approval_enabled:
                move.set_auto_approval_status('supplier_not_enabled', ['Supplier not enabled'])
                continue

            # roundoff- and residual products
            roundoff_product = move.get_roundoff_product()
            residual_product = move.get_residual_product()

            # validate some properties differently based on MTO or stock purchases
            mto_purchase = any(
                line.purchase_order_id.origin and line.purchase_order_id.origin.startswith(prefix)
                for prefix in ('SF', 'SB')
                for line in move.invoice_line_ids.filtered(lambda x: x.purchase_order_id is not False))

            vat_ok = all(
                line.tax_ids and len(line.tax_ids) == 1
                and line.account_id and line.account_id.tax_ids and len(line.account_id.tax_ids) == 1
                and line.tax_ids[0].id == line.account_id.tax_ids[0].id
                for line in move.invoice_line_ids.filtered(lambda x: x.display_type in ['product', False]))

            # account is OK if: standard account is not set, or all lines have the same account as the standard
            # all lines with real products (not line notes or sections) must have a financial account
            # if not financial account validation is selected, this should always validate to true
            account_ok = not move.partner_id.auto_approval_validate_account or all(
                not move.partner_id.standard_account and line.account_id
                or line.account_id and line.account_id.id == move.partner_id.standard_account.id
                for line in move.invoice_line_ids.filtered(lambda x: x.display_type in ['product', False])
            )

            # Define conditions with descriptions
            conditions_with_failed_msgs = [
                (move.partner_id, "Partner is not set"),
                (move.partner_shipping_id, "Partner Shipping is not set"),
                (move.ref, "Invoice number is not set"),
                (move.payment_reference if move.partner_id.auto_approval_validate_kid else not move.payment_reference,
                 "Payment reference is invalid based on KID requirement"),
                (move.product_type_id if mto_purchase else True, "Product type is not set"),
                (move.order_type if mto_purchase else True, "Order type is not set"),
                (move.invoice_date, "Invoice date is not set"),
                (move.date, "Accounting date is not set"),
                (move.invoice_date.month == move.date.month,
                 "Invoice date and accounting date are not in the same month"),
                (move.invoice_date_due, "Invoice due date is not set"),
                (move.invoice_date_due >= move.invoice_date, "Invoice due date is not after or on invoice date"),
                # Check for lines and connection to PO's, excluding sections/notes and specific products
                (all(line.purchase_line_id for line in move.invoice_line_ids.filtered(
                    lambda x: x.display_type in ['product', False] and x.product_id.id not in [roundoff_product.id, residual_product.id])),
                 "Not all invoice lines are connected to PO lines"),
                (vat_ok, 'VAT is not OK'),
                (account_ok, 'Account used in lines are not the same as on the supplier')
            ]

            # Check which conditions did not validate and create a list of their descriptions
            failed_conditions = [description for condition, description in conditions_with_failed_msgs if not condition]

            if not failed_conditions:
                move.set_auto_approval_status('validated')
            else:
                move.set_auto_approval_status('invalid', failed_conditions)

    def get_roundoff_product(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        default_round_off_product = ir_config_parameter.get_param('strai.round_off_product')
        roundoff_product = self.env['product.product'].browse(int(default_round_off_product))
        return roundoff_product

    @api.model
    def get_residual_product(self):
        residual_product = self.partner_id.residual_product if self.partner_id and self.partner_id.residual_product else \
        self.env['product.product'].search([('default_code', '=', 'Prisavvik')], limit=1)
        return residual_product

    def set_auto_approval_status(self, auto_approval_status, info=None):
        if info is None:
            info = []

        for move in self:
            move.auto_approval_status = auto_approval_status
            if auto_approval_status:
                move.auto_approved_timestamp = fields.datetime.now()
            elif auto_approval_status == 'new':
                move.auto_approved_timestamp = False

            if auto_approval_status == 'approved':
                # get OdooBot as the approver
                odoobot = self.env['res.users'].search([('login', '=', '__system__'), ('active', 'in', [True, False])])
                # set approver as the OdooBot to make it clear that this is automated
                move.approved_manager_user_id = odoobot.id
                move.manger_approved_date = fields.date.today()
                move.first_approval = False
                # also set as 2nd approver if applicable
                if move.second_approval_user_id:
                    move.approved_director_user_id = odoobot.id
                    move.director_approved_date = fields.date.today()
                    move.second_approval = False
                # remove previous errors
                move.auto_approval_info = False
                # post message to chatter
                move.message_post(body=_('Invoice automatically approved'))
            elif info and len(info) > 0:
                move.auto_approval_info = '\n'.join(info)

    def set_auto_post_status(self, auto_post_status):
        for move in self:
            move.auto_post_status = auto_post_status
