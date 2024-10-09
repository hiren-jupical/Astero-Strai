from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_type_id = fields.Many2one('product.type', store=True, readonly=False)
    product_category_id = fields.Many2one('product.category', related="product_id.categ_id", store=True)

    position = fields.Integer(string="pos")

    # order_type = fields.Selection(string="Order Type", related="move_id.order_type", readonly=False, store=True)

    order_type = fields.Selection(selection=[
        ('standard', 'Standard'),
        ('builder', 'Builder'),
        ('project', 'Project'),
        ('exhibit', 'Exhibition'),
        ('campaign', 'Campaign')
    ], string="Order Type", compute="_compute_order_type", store=True, readonly=False)

    purchase_order_price_unit = fields.Float(string="PO Unit Price", related="purchase_line_id.price_unit")
    purchase_order_qty_received = fields.Float(string="PO Qty Received", related="purchase_line_id.qty_received")
    validated = fields.Boolean()
    move_origin_type = fields.Selection(related='move_id.move_origin_type')
    price_inc_vat = fields.Monetary(compute='_compute_price_inc_vat', inverse='_inverse_compute_price_inc_vat', store=True, readonly=False, string='Ink MVA')
    is_complaint = fields.Boolean(string="Reklamasjon")

    sales_project_id = fields.Many2one('sales.projects', related='move_id.sales_project_id', string='Salgsprosjekt', store=True)
    apartment_id = fields.Many2one('sales.projects.apartment', related='move_id.apartment_id', string="Leilighet")

    invoice_user_id = fields.Many2one(
        string='Salesperson',
        comodel_name='res.users',
        related='move_id.invoice_user_id',
        store=True
    )

    product_brand_id = fields.Many2one('akustikken.product.brand', string='Brand', related="product_id.product_tmpl_id.product_brand_id", store=True, readonly=False)

    store_name = fields.Char(string="Butikk", related='purchase_order_id.store_name', store=True)

    def _inter_company_prepare_invoice_line_data(self):
        res = super(AccountMoveLine, self)._inter_company_prepare_invoice_line_data()
        res['position'] = self.position
        return res

    # This method is no longer available from version 16.
    # Overwrite compute method to include account_id from PO
    # @api.depends('product_id', 'account_id', 'partner_id', 'date')
    # def _compute_analytic_account_id(self):
    #     for record in self:
    #         if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
    #             rec = self.env['account.analytic.default'].account_get(
    #                 product_id=record.product_id.id,
    #                 partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
    #                 account_id=record.account_id.id,
    #                 user_id=record.env.uid,
    #                 date=record.date,
    #                 company_id=record.move_id.company_id.id
    #             )
    #             if rec and record.display_type not in ['line_section', 'line_note']:
    #                 record.analytic_account_id = rec.analytic_id

    @api.depends('price_unit', 'tax_ids')
    def _compute_price_inc_vat(self):
        for line in self:
            tax_percent = (line.tax_ids[0].amount if line.tax_ids and len(line.tax_ids) == 1 else 0) / 100.0
            line.price_inc_vat = line.price_unit * (1 + tax_percent)

    @api.onchange('price_inc_vat')
    def _inverse_compute_price_inc_vat(self):
        for line in self:
            tax_percent = (line.tax_ids[0].amount if line.tax_ids and len(line.tax_ids) == 1 else 0) / 100.0
            line.price_unit = line.price_inc_vat / (1 + tax_percent)

    @api.depends('move_id', 'move_id.order_type')
    def _compute_order_type(self):
        for line in self:
            line.order_type = line.move_id.order_type if line.move_id.order_type else line.order_type
