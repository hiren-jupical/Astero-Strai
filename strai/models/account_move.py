import base64
from odoo import models, fields, api, Command, _

from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    product_type_id = fields.Many2one('product.type', string="Product Type", store=True)

    pricelist_id = fields.Char(string='Pricelist', compute='_compute_pricelist_id')
    purchase_ref = fields.Char()
    remarks = fields.Char(string="Remarks", tracking=True)
    stria_purchase_id = fields.Many2one('purchase.order', string="purchase  Order")
    move_origin_type = fields.Selection([
        ('pdf', 'PDF'),
        ('ehf', 'EHF'),
        ('intercompany', 'Intercompany'),
    ], store=True, compute='compute_move_origin_type', readonly=False)
    warranty_selected = fields.Boolean(string='Reklamasjon')

    def _get_order_type(self):
        for order in self:
            if order.invoice_origin:
                sale = self.env['sale.order'].search([('name', 'ilike', order.invoice_origin)])
                purchase = self.env['purchase.order']
                if sale:
                    order.order_type = sale.order_type
                else:
                    purchase = self.env['purchase.order'].search([('name', 'ilike', order.invoice_origin)])
                if purchase:
                    order.order_type = purchase.order_type
                else:
                    order.order_type = False
            else:
                order.order_type = False

    order_type = fields.Selection(selection=[
        ('standard', 'Standard'),
        ('builder', 'Builder'),
        ('project', 'Project'),
        ('exhibit', 'Exhibition'),
        ('campaign', 'Campaign')
    ], string="Order Type", default=_get_order_type)
    auto_validated = fields.Selection([('approved', 'Approved'),
                                       ('rejected', 'Rejected')], string='Auto Validation')

    builder_partner_id = fields.Many2one('res.partner', domain="[('is_builder', '=', True)]")

    builder_agreement_situation = fields.Selection([
        ('builder_direct', 'Builder buys directly'),
        ('referral', 'Referral'),
        ('optional_customer', 'Optional customer')
    ])

    strai_analytic_account_id = fields.Many2one('account.analytic.account')

    sales_project_id = fields.Many2one('sales.projects', string='Salgsprosjekt')
    apartment_id = fields.Many2one('sales.projects.apartment', string="Apartment")

    exhibit_analytic_account_id = fields.Many2one('account.analytic.account')  # not used any longer
    price_campaign_id = fields.Many2one('strai.campaign',
                                        string="Campaign Pricelist",
                                        domain="['|', ('campaign_company_ids', 'in', company_id), ('campaign_company_ids', '=', False)]")
    store_user_name = fields.Char("Selger butikk")

    store_warranty_order = fields.Boolean(string="Selgerfeil")
    store_name = fields.Char("Butikk")

    winner_reference = fields.Char(string="Winner Butikk", readonly=True)

    # should be easy to see on what invoices products are received, to know which one is ready to be approved/validated
    product_receipt_status = fields.Selection([
        ('no', 'Ikke mottatt'),
        ('partial', 'Delvis mottatt'),
        ('complete', 'Mottatt'),
        ('not_applicable', 'Ikke relevant')
    ], string="Varemottak", default='no', compute='compute_product_receipt_status', store=True)

    invoice_user_id = fields.Many2one(compute='_compute_invoice_user_id', store=True)

    orderinfo1 = fields.Char(string='Ordreinfo 1', compute='_compute_orderinfo1', store=True)
    orderinfo2 = fields.Char(string='Ordreinfo 2', compute='_compute_orderinfo2', store=True)

    @api.onchange('order_type')
    def _change_pricelist_order_type(self):
        # Reset fields on changing order_type
        for record in self:
            if record.order_type != 'project':
                record.sales_project_id = False
                record.apartment_id = False
            if record.order_type != 'campaign':
                record.price_campaign_id = False
            if record.order_type != 'builder':
                record.builder_partner_id = False
                record.builder_agreement_situation = False

    @api.depends('order_type', 'builder_partner_id', 'sales_project_id', 'exhibit_analytic_account_id',
                 'price_campaign_id')
    def _compute_orderinfo1(self):
        for rec in self:
            if rec.order_type:
                rec.orderinfo1 = False
            if rec.builder_partner_id:
                rec.orderinfo1 = rec.builder_partner_id.name
            elif rec.sales_project_id:
                rec.orderinfo1 = rec.sales_project_id.name
            elif rec.exhibit_analytic_account_id:
                rec.orderinfo1 = rec.exhibit_analytic_account_id.name
            elif rec.price_campaign_id:
                rec.orderinfo1 = rec.price_campaign_id.name

    @api.depends('order_type', 'builder_agreement_situation', 'apartment_id')
    def _compute_orderinfo2(self):
        for rec in self:
            if rec.order_type:
                rec.orderinfo2 = False
            if rec.builder_agreement_situation:
                rec.orderinfo2 = dict(
                    self.fields_get(allfields=['builder_agreement_situation'])['builder_agreement_situation']
                    ['selection']).get(rec.builder_agreement_situation)
            elif rec.apartment_id:
                rec.orderinfo2 = rec.apartment_id.name

    def _compute_pricelist_id(self):
        for order in self:
            if order.invoice_origin:
                sale = self.env['sale.order'].search([('name', 'ilike', order.invoice_origin)])
                company = self.env['res.company']._find_company_from_partner(order.partner_id.id)
                external_vendor = False
                order.pricelist_id = False
                if not company:
                    external_vendor = True
                    company = sale.company_id
                if sale.order_type == 'builder' and sale.builder_partner_id:
                    order.pricelist_id = sale.builder_partner_id.sudo().with_company(company).internal_pricelist_id.name
                if sale.order_type == 'campaign' and sale.price_campaign_id:
                    order.pricelist_id = sale.price_campaign_id.sudo().with_company(company).campaign_pricelist_id.name
                if sale.order_type in ['standard', 'exhibit']:
                    # order_type = 'standard' if sale.order_type == 'warranty' else sale.order_type
                    order_type = sale.order_type
                    order.pricelist_id = sale.env['product.pricelist'].sudo().search([('company_id', '=', company.id), ('order_type', '=', order_type)], limit=1).name
                if sale.order_type == 'project':
                    apartment_count = sale.sales_project_id.apartment_count
                    if apartment_count >= 10:
                        order.pricelist_id = sale.env['product.pricelist'].sudo().search([('company_id', '=', company.id), ('order_type', '=', sale.order_type)], limit=1).name
                    if apartment_count < 10:
                        order.pricelist_id = sale.sales_project_id.developer_id.with_company(company).internal_pricelist_id.name
                # if external_vendor and order.pricelist_id.purchase_pricelist_id:
                #     order.pricelist_id = order.pricelist_id.purchase_pricelist_id.name
            else:
                order.pricelist_id = False

    def _post(self, soft=True):
        # OVERRIDE to generate cross invoice based on company rules.
        # copy of original, checking sale and purchase in addition to invoice and refund
        # check this function in future upgrades
        invoices_map = {}
        posted = super()._post(soft)
        for invoice in posted.filtered(lambda move: move.is_invoice()):
            company = self.env['res.company']._find_company_from_partner(invoice.partner_id.id)
            if company and company.rule_type == 'sale_purchase' and not invoice.auto_generated:
                invoices_map.setdefault(company, self.env['account.move'])
                invoices_map[company] += invoice
        for company, invoices in invoices_map.items():
            context = dict(self.env.context, default_company_id=company.id)
            context.pop('default_journal_id', None)
            invoices.with_user(company.intercompany_user_id).with_context(context).with_company(company)._inter_company_create_invoices()

        # validate purchase orders, set analytic account on head and on lines
        for inv in posted:
            intercompany_invoices = self.env['account.move'].sudo().search([('company_id.partner_id', '=', inv.commercial_partner_id.id), ('ref', '=', inv.name), ('partner_id', '=', inv.company_id.id), ('move_type', 'in', ['in_invoice', 'in_refund'])])

            if inv.ref and inv.move_type in ['in_invoice']:
                same_ref_bill = self.env['account.move'].sudo().search([('ref', '=', inv.ref), ('id', '!=', inv.id), ('partner_id', '=', inv.partner_id.id), ('move_type', 'in', ['in_invoice'])])
                if same_ref_bill:
                    raise UserError(_("Error! A bill with the same reference already exists in the system for this vendor"))

            # set analytic account
            # cancel out intercompany zero invoices
            for interinvoice in intercompany_invoices:
                if interinvoice.move_type in ['in_invoice'] and interinvoice.stria_purchase_id:
                    for line in interinvoice.invoice_line_ids:
                        line.analytic_distribution = line.purchase_line_id.analytic_distribution if line.purchase_line_id else interinvoice.stria_purchase_id.order_line[0].analytic_distribution if len(interinvoice.stria_purchase_id.order_line) > 0 else line.analytic_distribution
                        if not interinvoice.strai_analytic_account_id and line.analytic_distribution:
                            interinvoice.strai_analytic_account_id = int(list(line.analytic_distribution.keys())[0])
            intercompany_invoices._validate_purchase_order()

            # find correct attachment (the newly created invoice) and mark it as the main document, to get the preview in Odoo correct (otherwise, it will show attachments that were added before posting)
            for attachment in inv.attachment_ids:
                if attachment.name == f'{inv.name.replace("/", "_")}.pdf':
                    inv.message_main_attachment_id = attachment
                    break

            # Handle "Reklamasjonsbestilling fra butikk" by setting all item lines to zero by setting the discount to 100
            for interinvoice in intercompany_invoices.filtered(lambda x: x.store_warranty_order == True):
                amount_untaxed = interinvoice.amount_untaxed
                is_posted = interinvoice.state == 'posted'
                if is_posted:
                    interinvoice.state = 'draft'
                for line in interinvoice.invoice_line_ids.filtered(lambda y: y.display_type not in ['line_section', 'line_note']):
                    line.discount = 100
                    analytic_distribution = False
                    strai_analytic_account = False
                    if line.analytic_distribution:
                        analytic_distribution = line.analytic_distribution  # pick one of them that are set (should be the same for all)
                    if line.strai_analytic_account_id:
                        strai_analytic_account = line.strai_analytic_account_id  # pick one of them that are set (should be the same for all)
                if is_posted:
                    interinvoice.state = 'posted'

                # and add the warranty product
                complaint_product_id = interinvoice.company_id.warranty_product_id
                if complaint_product_id:
                    line_values = {
                        'move_id': interinvoice.id,
                        'product_id': complaint_product_id.id,
                        'quantity': 1,
                        'price_unit': amount_untaxed,
                        'is_complaint': True,
                        'analytic_distribution': analytic_distribution,
                        'strai_analytic_account_id': strai_analytic_account.id
                    }
                    interinvoice.invoice_line_ids.create(line_values)

            # automatically cancel out zero invoices
            for interinvoice in intercompany_invoices.filtered(lambda x: x.amount_total == 0.0 and not x.store_warranty_order ):
                interinvoice.button_cancel()
                interinvoice.unlink()

        return posted

    def _validate_purchase_order(self):
        """ Validates purchase orders by matching account_move_lines with purchase_order_lines
            Uses product_ids, qty_recieved(PO lines) = quantity(account_move_lines), and prices to match lines.
            If one line can not be matched (for example qty_recieved for a line on PO is 0 and quantity on account_move_line is 1),
            it will be rejected and PO and vendor bill will not be automatically matched.
        """
        for inv in self:
            # Remove inv.ref related code and used inv.stria_purchase_id
            if inv.move_type in ['in_invoice'] and inv.stria_purchase_id:
                all_validated = True
                po = inv.stria_purchase_id
                invoice_lines = inv.invoice_line_ids.filtered(lambda x: x.display_type in ['product', False])
                po_lines = po.order_line.filtered(lambda x: x.display_type in ['product', False])
                for inv_line in invoice_lines:
                    po_line_id = po_lines.filtered(lambda x: x.position == inv_line.position and x.product_id.id == inv_line.product_id.id)
                    if len(po_line_id) == 1:
                        line_validated = (po_line_id.product_id.id == inv_line.product_id.id
                                          and po_line_id.product_qty == inv_line.quantity
                                          and po_line_id.price_unit == inv_line.price_subtotal)  # compare price ex vat inc discount from invoice with price from po line
                        inv_line.purchase_line_id = po_line_id.id
                    else:
                        line_validated = False
                    inv_line.validated = line_validated
                    if not line_validated:
                        all_validated = False
                if all_validated:
                    inv.update({
                        'auto_validated': 'approved',
                    })
                    msg = _("Automatically matched the vendor bill with the corresponding purchase order \
                          (<a href='#' data-oe-model='purchase.order' data-oe-id='%d'>%s</a>)<br/> \
                          Invoice is posted automatically")

                    inv._post()
                    po._compute_invoice()
                else:
                    inv.update({
                        'auto_validated': 'rejected',
                    })
                    msg = _("Could not automatically match the vendor bill with the corresponding purchase order \
                          (<a href='#' data-oe-model='purchase.order' data-oe-id='%d'>%s</a>)<br/> \
                          Manual action is required")
                    # inv.activity_schedule(
                    #     'account_invoice_intercompany.invoice_act_match_error',
                    #     user_id=self.env.user.id,
                    #     note=_(msg % (po.id, po.name)),
                    #     date_deadline=inv.invoice_date_due
                    # )
                inv.message_post(body=msg % (po.id, po.name))

    def _inter_company_prepare_invoice_data(self, invoice_type):
        res = super(AccountMove, self)._inter_company_prepare_invoice_data(invoice_type)
        if invoice_type in ['in_invoice', 'in_refund']:
            # get original invoice and copy attachments
            res.update({'attachment_ids': []})
            orig_inv = self.env['account.move'].browse(res['auto_invoice_id'])
            for attachment in orig_inv.attachment_ids.filtered(lambda x: not x.name.lower().endswith('.xml')):
                att_obj = {
                    'name': attachment.name,
                    'type': 'binary',
                    'datas': attachment.datas,
                    'res_model': 'account.move'
                }
                res['attachment_ids'].append((0, 0, att_obj))
            report, report_type = self.env['ir.actions.report']._render('account.report_invoice', self.ids)
            main_invoice_name = f'{self.name.replace("/", "_")}.pdf'
            if main_invoice_name not in [att[2]['name'] for att in res['attachment_ids']]:
                # add generated invoice
                att_obj = {
                    'name': main_invoice_name,
                    'type': 'binary',
                    'datas': base64.encodebytes(report),
                    'res_model': 'account.move'
                }
                res['attachment_ids'].append((0, 0, att_obj))
            partner_id = self.env['res.partner'].browse(res['partner_id'])
            if partner_id and partner_id.bank_ids[0]:
                res.update({'partner_bank_id': partner_id.bank_ids[0]})

        res.update({'order_type': self.order_type,
                    'product_type_id': self.product_type_id.id,
                    'price_campaign_id': self.price_campaign_id.id,
                    'strai_analytic_account_id': self.exhibit_analytic_account_id.id,
                    'builder_partner_id': self.builder_partner_id.id,
                    'builder_agreement_situation': self.builder_agreement_situation,
                    'sales_project_id': self.sales_project_id.id,
                    'apartment_id': self.apartment_id.id,
                    'stria_purchase_id': self.stria_purchase_id.id,
                    'store_user_name': self.store_user_name,
                    'ref': self.name,
                    'store_warranty_order': self.store_warranty_order,
                    'winner_reference': self.winner_reference
                    })

        return res

    # This functionality is already introduced not required to override this method.
    # Removes account_id on notes and section lines because they would appear on analytic account, which makes no sense.
    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(AccountMove, self).create(vals_list)
    #     for rec in res:
    #         for line in rec.invoice_line_ids.filtered(lambda x: x.display_type in ['line_section', 'line_note']):
    #             line.analytic_distribution = False

    #     return res

    @api.onchange('partner_id')
    def onchange_partner_fill_bank(self):
        if self.move_type == 'in_invoice':
            if self.partner_id and self.partner_id.bank_ids:
                self.partner_bank_id = self.partner_id.bank_ids[0] if self.partner_id.bank_ids else False
            if not self.partner_id:
                self.partner_bank_id = False
        elif self.move_type == 'out_invoice':
            self.partner_bank_id = self.company_id.bank_ids[0] if self.company_id.bank_ids else False

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        purchase_order_id = self.purchase_vendor_bill_id.purchase_order_id or self.purchase_id
        vendor_bill = self.purchase_vendor_bill_id.vendor_bill_id
        if purchase_order_id:
            self.product_type_id = purchase_order_id.product_type_id
            self.order_type = purchase_order_id.order_type
            self.price_campaign_id = purchase_order_id.price_campaign_id
            self.sales_project_id = purchase_order_id.sales_project_id
            self.apartment_id = purchase_order_id.apartment_id
            self.builder_partner_id = purchase_order_id.builder_partner_id
            self.builder_agreement_situation = purchase_order_id.builder_agreement_situation
            self.store_name = purchase_order_id.store_name
            self.winner_reference = purchase_order_id.winner_reference
        elif vendor_bill:
            self.product_type_id = vendor_bill.product_type_id
            self.order_type = vendor_bill.order_type
            self.price_campaign_id = vendor_bill.price_campaign_id
            self.sales_project_id = vendor_bill.sales_project_id
            self.apartment_id = vendor_bill.apartment_id
            self.builder_partner_id = vendor_bill.builder_partner_id
            self.builder_agreement_situation = vendor_bill.builder_agreement_situation
            self.store_name = vendor_bill.store_name
            self.winner_reference = vendor_bill.winner_reference
        return super()._onchange_purchase_auto_complete()

    @api.onchange('strai_analytic_account_id')
    def onchange_exhibit_account(self):
        if self.strai_analytic_account_id:
            for line in self.invoice_line_ids:
                line.analytic_distribution = {str(self.strai_analytic_account_id.id): 100}

    @api.depends('auto_invoice_id', 'attachment_ids')
    def compute_move_origin_type(self):
        for move in self:
            if move.auto_invoice_id:
                move.move_origin_type = 'intercompany'
            elif len(move.attachment_ids.filtered(lambda x: x.name.endswith('.xml'))) > 0:
                move.move_origin_type = 'ehf'
            else:
                move.move_origin_type = 'pdf'

    # warranty_product_id should be added to the invoice lines
    def action_add_complaint(self):
        for invoice in self:
            complaint_product_id = invoice.company_id.warranty_product_id
            complaint_line = invoice.invoice_line_ids.filtered(lambda l: l.is_complaint)
            if complaint_line:
                complaint_line.unlink()
            if invoice.warranty_selected and complaint_product_id:
                line_values = {
                    'product_id': complaint_product_id.id,
                    'quantity': -1,
                    'price_unit': invoice.amount_untaxed,
                    'is_complaint': True,
                }
                invoice.invoice_line_ids = [Command.create(line_values)]

    @api.onchange('apartment_id')
    def onchange_apartment_id(self):
        for record in self:
            if record.apartment_id and record.apartment_id.analytic_account_id:
                record.strai_analytic_account_id = record.apartment_id.analytic_account_id

    @api.depends('invoice_line_ids', 'invoice_line_ids.purchase_line_id', 'invoice_line_ids.purchase_line_id.qty_received')
    def compute_product_receipt_status(self):
        for inv in self:
            inv.product_receipt_status = \
                'not_applicable' if all(
                    line.purchase_line_id.id is False
                    for line in inv.invoice_line_ids) else \
                'no' if all(
                    line.purchase_line_id.qty_received == 0.0
                    for line in inv.invoice_line_ids.filtered(lambda x: x.purchase_line_id.id is not False)) else \
                'complete' if all(
                    line.purchase_line_id.qty_received > 0.0
                    for line in inv.invoice_line_ids.filtered(lambda x: x.display_type in ['product', False] and x.purchase_line_id.id is not False)) else \
                'partial'

    @api.depends('invoice_line_ids.analytic_distribution')
    def _compute_invoice_user_id(self):
        for move in self:
            analytic_distribution = next((line.analytic_distribution for line in move.invoice_line_ids if line.analytic_distribution), False)

            # get the first analytic account set on invoice
            analytic_account_id = int(list(analytic_distribution.keys())[0]) if analytic_distribution and len(analytic_distribution.keys()) >= 1 else False

            if analytic_account_id:
                # get last sale order that was used with this analytic account id
                saleorder = self.env['sale.order'].search([('analytic_account_id', '=', analytic_account_id)], order='create_date desc', limit=1)
                if saleorder:
                    move.invoice_user_id = saleorder.user_id.id if saleorder.user_id else move.invoice_user_id

    def action_change_to_warranty_product_id(self):
        for inv in self:
            amount_untaxed = inv.amount_untaxed
            analytic_distribution = False
            strai_analytic_account = False
            for line in inv.invoice_line_ids.filtered(lambda y: y.display_type not in ['line_section', 'line_note']):
                line.discount = 100
                if line.analytic_distribution:
                    analytic_distribution = line.analytic_distribution  # pick one of them that are set (should be the same for all)
                if line.strai_analytic_account_id:
                    strai_analytic_account = line.strai_analytic_account_id  # pick one of them that are set (should be the same for all)

            # and add the warranty product
            complaint_product_id = inv.company_id.warranty_product_id
            if complaint_product_id:
                line_values = {
                    'move_id': inv.id,
                    'product_id': complaint_product_id.id,
                    'quantity': 1,
                    'price_unit': amount_untaxed,
                    'is_complaint': True,
                    'analytic_distribution': analytic_distribution,
                    'strai_analytic_account_id': strai_analytic_account.id if strai_analytic_account else False
                }
                inv.invoice_line_ids.create(line_values)

    def action_change_to_pass_through_billing_product_id(self):
        for inv in self:
            amount_untaxed = inv.amount_untaxed
            analytic_distribution = False
            strai_analytic_account = False
            for line in inv.invoice_line_ids.filtered(lambda y: y.display_type not in ['line_section', 'line_note']):
                line.discount = 100
                if line.analytic_distribution:
                    analytic_distribution = line.analytic_distribution  # pick one of them that are set (should be the same for all)
                if line.strai_analytic_account_id:
                    strai_analytic_account = line.strai_analytic_account_id  # pick one of them that are set (should be the same for all)

            # and add the warranty product
            pass_through_billing_product_id = inv.company_id.pass_through_billing_product_id
            if pass_through_billing_product_id:
                line_values = {
                    'move_id': inv.id,
                    'product_id': pass_through_billing_product_id.id,
                    'quantity': 1,
                    'price_unit': amount_untaxed,
                    'analytic_distribution': analytic_distribution,
                    'strai_analytic_account_id': strai_analytic_account.id if strai_analytic_account else False
                }
                inv.invoice_line_ids.create(line_values)
