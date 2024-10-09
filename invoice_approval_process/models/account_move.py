from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    # notes by approver
    invoice_remark = fields.Text(string='Invoice Remarks')

    # fields for check triple apply is enabled in configuration(for hide approval info page when disabled)
    vendor_triple_approval_enabled = fields.Boolean(string='Vendor Triple Approval Enabled', compute='_compute_triple_approval_enabled')

    # fields for manager or director approval process checking
    first_approval = fields.Boolean('First Approval', copy=False, compute='_compute_first_approval', store=True)
    second_approval = fields.Boolean('Second Approval', copy=False, compute='_compute_second_approval', store=True)

    # manager and director group user id fields
    first_approval_user_id = fields.Many2one('res.users', store=True, string='Manager Approval', copy=False)
    second_approval_user_id = fields.Many2one('res.users', store=True, string='Director Approval', copy=False)

    # these fields will store, invoice approved manager or directors ids (current users id) (first approve - Manager,
    # second approve - Director)
    approved_manager_user_id = fields.Many2one('res.users', string='Approved Manager', readonly=True, copy=False)
    approved_director_user_id = fields.Many2one('res.users', string='Approved Director', readonly=True, copy=False)
    # approved date will store in these fields
    manger_approved_date = fields.Date(string='Manager Approved Date', readonly=True, copy=False)
    director_approved_date = fields.Date(string='Director Approved Date', readonly=True, copy=False)

    # define a field to know which invoices are calculated approver on, and which is ready for it
    invoice_approver_calculated = fields.Boolean(default=False)

    # compute invoice approver
    # 1. Try to connect the invoice to a purchase order
    #       if success, connect purchase person to approve the invoice
    # 2. If no purchase person is found, use person defined as default approver for the supplier
    # 3. If no other is found, set default from company
    # second approver is set by getting the specified 2. approver from the supplier
    # if no second approver there, look at default second approver on company level
    # if no one there either, do not use 2. approval

    def _cron_compute_invoice_approver(self, limit):
        # get Trunk processed invoices and intercompany invoices
        moves = self.env['account.move'].search(['&', '|', ('trunk_ocr_status', '=', 'processed'), ('auto_invoice_id', '!=', False), '&', ('invoice_approver_calculated', '=', False), ('move_type', 'in', ['in_invoice', 'in_refund'])], limit=limit)
        moves.compute_invoice_approver()

    def compute_invoice_approver(self, overwrite=False):
        for move in self:
            # do not override if set before, or set manually
            if move.first_approval_user_id and not overwrite:
                move.invoice_approver_calculated = True
                continue
            elif overwrite:
                # set false, to allow to be set to someone else
                move.first_approval_user_id = False

            # all invoices should be approved by someone
            move.first_approval = True
            # connect PO responsible person when available, if configured on company
            if move.company_id.po_responsible_person:
                # get move lines that are connected to purchase order lines
                move_lines_from_pos = move.invoice_line_ids.filtered(lambda x: x.purchase_order_id and x.purchase_order_id.user_id) if move.invoice_line_ids and len(move.invoice_line_ids) > 0 else False
                if move_lines_from_pos and len(move_lines_from_pos) > 0:
                    move.first_approval_user_id = move_lines_from_pos[0].purchase_order_id.user_id

            # connect approver from supplier if no person was found on PO / no PO connected
            if not move.first_approval_user_id:
                move.first_approval_user_id = move.partner_id.with_company(move.company_id).purchase_responsible_person_id

            # set 2. approver regardless of 1. approver, first from supplier
            move.second_approval_user_id = move.partner_id.with_company(move.company_id).force_director_approval

            # fallback to default approver on company
            if not move.first_approval_user_id:
                move.first_approval_user_id = move.company_id.manager_approval_user_id_vendor
            if not move.second_approval_user_id:
                move.second_approval_user_id = move.company_id.director_approval_user_id_vendor

            if move.second_approval_user_id:
                move.second_approval = True

            # should not re-calculate invoice at any time, if an approver
            if move.first_approval_user_id:
                move.invoice_approver_calculated = True

    def _compute_triple_approval_enabled(self):
        """Check and assign values, if triple approval enabled in specific invoice types"""
        for record in self:
            record.update({
                'vendor_triple_approval_enabled': record.company_id.enable_vendor_triple_approval,
            })

    def action_first_approval(self):
        """First approval action with necessary fields update"""
        for rec in self:
            if not rec.first_approval_user_id:
                raise UserError(_("Please set Approve by Manager."))
            if rec.first_approval_user_id and rec.first_approval_user_id.id != self.env.user.id:
                raise UserError(
                    _("Only %s can give Manager Approval to this invoice.") % rec.first_approval_user_id.name)

            rec.update({
                'first_approval': False,
                'approved_manager_user_id': self.env.user.id,
                'manger_approved_date': fields.date.today(),
            })

    def action_second_approval(self):
        """second approval action with necessary fields update"""
        for rec in self:
            if not rec.second_approval_user_id:
                raise UserError(_("Please set the Director approval user same as login user."))
            if rec.second_approval_user_id and rec.second_approval_user_id.id != self.env.user.id:
                raise UserError(_(
                    "Only %s can give Director Approval to this invoice.") % rec.second_approval_user_id.name)
            rec.update({
                'second_approval': False,
                'approved_director_user_id': self.env.user.id,
                'director_approved_date': fields.date.today(),
            })

    def action_post(self):
        # Evaluate if current user has the accountant user group
        can_confirm_bill = self.env.user.has_group('invoice_approval_process.group_can_confirm_bill')

        for inv in self:
            # If it is an incoming invoice/refund/receipt and the user does not have the accountant user group, throw and error
            if not can_confirm_bill and inv.move_type in ['in_invoice', 'in_refund', 'in_receipt']:
                raise UserError("Du har ikke tilgang til å postere inngående fakturaer")
            if not inv.partner_bank_id and inv.journal_id.type in ['sale', 'purchase'] and inv.move_type not in ['in_refund', 'out_refund']:
                raise ValidationError(_('Kontonummer må fylles ut før postering'))

        # Call the super to complete to posting
        return super(AccountMove, self).action_post()

    @api.depends('first_approval_user_id')
    def _compute_first_approval(self):
        for move in self:
            # always force minimum of 1 approver. If it is not approved, it should be
            if move.move_type in ['in_invoice', 'in_refund'] and not move.approved_manager_user_id:
                move.first_approval = True
            else:
                move.first_approval = False

    @api.depends('second_approval_user_id')
    def _compute_second_approval(self):
        for move in self:
            if move.move_type in ['in_invoice', 'in_refund'] and move.second_approval_user_id and not move.approved_director_user_id:
                move.second_approval = True
            else:
                move.second_approval = False
