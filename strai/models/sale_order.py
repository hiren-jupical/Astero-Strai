from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging
import time
from time import strftime
import datetime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import holidays
from ..helper.company import Company
from ..helper.payment_term import PaymentTerm
from ..helper.delivery_floor import DeliveryFloor
from ..helper.delivery_method import DeliveryMethod
from ..helper.delivery_type import DeliveryType
from ..helper.activity_type import ActivityType
from ..helper.res_user import ResUser
import re
from odoo.tools import float_compare
from collections import defaultdict
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import groupby



from ...trunk_queue.helper.trunk_queue_enum import TaskType

_logger = logging.getLogger(__name__)

ENDPOINT_BOOK_CAPACITY = '/Rainbow/AllocateManufacturingTimeSlot'
ENDPOINT_ORDER_DEADLINE = '/Order/GetOrderDeadline'
ENDPOINT_DELETE = '/Rainbow/DeleteAllocatedManufacturingTimeSlot/'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # New Info fields meant for customer to fill out:
    delivery_phone_one = fields.Char()
    delivery_phone_two = fields.Char()
    info_transport = fields.Text(string="Transport Comment", tracking=True)
    info_production = fields.Text(string="Production Comment", tracking=True)
    info_accounting = fields.Text(string="Accounting Comment", tracking=True)
    delivery_floor_id = fields.Many2one('delivery.floor', string="Delivery Floor", store=True, tracking=True)

    # Delivery Type
    delivery_type_id = fields.Many2one('delivery.type', string="Type of Car", tracking=True)
    delivery_method_id = fields.Many2one('delivery.method', string="Delivery Method", tracking=True)

    # Product Type
    product_type_id = fields.Many2one('product.type', string="Product Type", store=True)
    order_attachment_ids = fields.Many2many('ir.attachment', compute="_compute_order_attachements", string="Attachment")
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True, copy=False, default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    store_responsible_id = fields.Many2one('res.users', string="Att. butikk")

    visma_project = fields.Integer(required=False)  # not in use, can be deleted. Kept to keep history for now
    winner_reference_production = fields.Char("Winner Production", required=False)
    origin_sales_order_no = fields.Char("Origin sales order no")
    strai_revenue = fields.Monetary(string="Revenue", compute="_compute_contribution_margin", store=True)
    strai_cost = fields.Monetary(string="Cost", readonly=True)
    strai_contribution_margin = fields.Monetary(string="Contribution Margin", compute="_compute_contribution_margin", store=True)
    strai_contribution = fields.Float(string="Contribution %",compute="_compute_contribution_margin", store=True)

    # Override entire field to set 'signed' and 'reserved' state in the middle
    state = fields.Selection(
        selection_add = [
            ('draft', 'Quotation'),
            ('sent', 'Quotation Sent'),
            ('signed', 'Signed'),
            ('reserved', 'Reserved'),
            ('sale', 'Sales Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    date_signed = fields.Date()
    timestamp_confirmed = fields.Datetime()

    sales_project_id = fields.Many2one('sales.projects', string='Salgsprosjekt')
    apartment_id = fields.Many2one('sales.projects.apartment', string="Apartment")

    order_type = fields.Selection(selection=[
        ('standard', 'Standard'),
        ('builder', 'Builder'),
        ('project', 'Project'),
        ('exhibit', 'Exhibition'),
        ('campaign', 'Campaign')
    ], string="Order Type")

    exhibit_analytic_account_id = fields.Many2one('account.analytic.account')
    sale_to_self = fields.Boolean(default=False)
    warranty_identification = fields.Char()
    warranty_selected = fields.Boolean(string="Warranty")
    builder_partner_id = fields.Many2one('res.partner', domain="[('is_builder', '=', True)]")
    this_day = fields.Date(default=fields.Datetime.now)
    price_campaign_id = fields.Many2one('strai.campaign',
                                        string="Campaign Pricelist",
                                        domain="['&', '&', ('from_date', '<=', this_day), ('to_date', '>=', this_day), '|', ('campaign_company_ids', 'in', company_id), ('campaign_company_ids', '=', False)]")

    winner_reference = fields.Char(string="Winner", readonly=True)
    winner_file_id = fields.Char(default="1")
    winner_last_updated = fields.Datetime()
    winner_production_last_updated = fields.Datetime()
    winner_file_new_version_required = fields.Boolean(default=False)
    delivery_confirmed = fields.Boolean(default=False)
    delivery_completed = fields.Boolean(default=False)
    external_sales_order_no = fields.Char(readonly=True, string="External Orderno.")
    is_production = fields.Boolean(related="company_id.production")
    client_ref = fields.Char()
    # Fake_field used as an invisible readonly field, placed above winner_reference to keep label and field together in view. Could not solve problem otherwise.
    fake_field = fields.Char()

    booked_by_store = fields.Boolean()
    is_confirmed = fields.Boolean(default=False)
    capacity = fields.Selection([
        ('good', 'Good Capacity'),
        ('low', 'Low Capacity'),
        ('no_capacity', 'No Capacity'),
    ], compute='_compute_capacity')
    capacity_booking_deadline = fields.Date(compute='_compute_capacity_from_date', store=True)
    production_date = fields.Datetime()

    remarks = fields.Char(string="Kundemerknad")

    eno = fields.Boolean(default=False, string='ENO')

    store_name = fields.Char("Butikk")
    store_user_name = fields.Char(string="Selger butikk", compute="_compute_store_user_name", store=True)
    store_user_email = fields.Char("E-post selger butikk")

    builder_agreement_situation = fields.Selection([
        ('builder_direct', 'Builder buys directly'),
        ('referral', 'Referral'),
        ('optional_customer', 'Optional customer')
    ])

    orderinfo1 = fields.Char(string='Ordreinfo 1', compute='_compute_orderinfo1', store=True)
    orderinfo2 = fields.Char(string='Ordreinfo 2', compute='_compute_orderinfo2', store=True)

    # transport date from ordreboka, the date when the final order (entire sale order) is sent from HUB
    logistic_send_date = fields.Date()
    # sale order is produced on the Evert production line at this date
    productionline_date = fields.Date()
    sales_project_status = fields.Selection(string="Salgsprosjektstatus", store=True, related='sales_project_id.status')

    norwegian_holidays = holidays.country_holidays('NO')

    partner_shipping_id = fields.Many2one(tracking=True)

    sales_rep_affiliated_store = fields.Many2one('res.partner', domain="[('category_id', 'child_of', 'Selger')]", string="Att. forhandler/B2B")
    store_warranty_order = fields.Boolean(string="Selgerfeil")
    #independent_shop = fields.Boolean(related="partner_id.independent_shop")
    is_strai_store = fields.Boolean(string="Straibutikk", compute="_compute_is_strai_store", store=True)

    order_change_cutoff_date = fields.Datetime(string="Rettefrist", compute="_compute_order_change_cutoff_date", store=True)

    commitment_date = fields.Datetime(tracking=True)

    # COMPUTE METHODS
    @api.depends('order_type', 'builder_partner_id', 'sales_project_id', 'exhibit_analytic_account_id',
                 'price_campaign_id')
    def _compute_orderinfo1(self):
        for order in self:
            if order.order_type:
                order.orderinfo1 = False
            if order.builder_partner_id:
                order.orderinfo1 = order.builder_partner_id.name
            elif order.sales_project_id:
                order.orderinfo1 = order.sales_project_id.name
            elif order.exhibit_analytic_account_id:
                order.orderinfo1 = order.exhibit_analytic_account_id.name
            elif order.price_campaign_id:
                order.orderinfo1 = order.price_campaign_id.name


############################### Created Virtual PO for Calculate Contribution Margin ##########################################################

    @api.depends('amount_untaxed','strai_revenue', 'strai_cost','strai_contribution_margin', 'strai_contribution')
    def _compute_contribution_margin(self):
        for rec in self:
            if rec.amount_untaxed:
                rec.strai_revenue = rec.amount_untaxed
                rec.strai_contribution_margin = (rec.strai_revenue - rec.strai_cost)
                rec.strai_contribution = (rec.strai_contribution_margin / rec.strai_revenue) * 100

    def action_create_po(self):
        self.strai_cost = 0.0
        for rec in self.order_line:
            so_po_val = rec.so_line_get_po_val()

    def get_po_vals(self,po_vals):
        for rec in po_vals:
            for line in rec.order_line:
                line._compute_price_unit_and_date_planned_and_name()
                line.update_price_before_discount()
                line._onchange_price_unit()
                line._onchange_discount()
                self.strai_cost += rec.amount_untaxed


###############################################################################################################################################
        
            

    @api.depends('order_type', 'builder_agreement_situation', 'apartment_id')
    def _compute_orderinfo2(self):
        for order in self:
            if order.order_type:
                order.orderinfo2 = False
            if order.builder_agreement_situation:
                order.orderinfo2 = dict(
                    self.fields_get(allfields=['builder_agreement_situation'])['builder_agreement_situation']
                    ['selection']).get(order.builder_agreement_situation)
            elif order.apartment_id:
                order.orderinfo2 = order.apartment_id.name

    def _compute_order_attachements(self):
        for order in self:
            order.order_attachment_ids = self.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=', order.id), ('is_sale_attachment', '=', True)])

    def action_assign(self):
        self.user_id = self.env.user.id

    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft', 'sent', 'signed', 'reserved'}

    # Check required fields
    def _action_confirm(self):
        for order in self:
            seq_count = 0
            if order.state == 'sale':
                missing_fields = []
                if order.delivery_method_id.id == DeliveryMethod.DeliverToCustomer.value and (not order.partner_shipping_id or not self._validate_delivery_address(order.partner_shipping_id)):
                    missing_fields.append(_("Ugyldig leveringsdadresse. Leveringsadressen må oppdateres i Winner, og  Winner må eksporteres på nytt"))
                if not self._validate_customer_address(order.partner_id):
                    missing_fields.append(_('Ugyldig kundeadresse. Kundeadressen må oppdateres i Winner, og Winner må eksporteres på nytt'))
                if (not order.delivery_phone_one or not re.match(r"^[0-9]\d{7}$", "{}".format(order.delivery_phone_one))) and order.order_type != 'exhibit':
                    missing_fields.append(_("Delivery phone one (8 Digits)"))
                if order.delivery_phone_two and not re.match(r"^[0-9]\d{7}$", "{}".format(order.delivery_phone_two)):
                    missing_fields.append(_("Delivery phone two (8 Digits)"))
                if not order.product_type_id:
                    missing_fields.append(_("Product Type"))
                if not order.order_type:
                    missing_fields.append(_("Order Type"))
                if not order.delivery_method_id and order.order_type != 'exhibit':
                    missing_fields.append(_("Delivery Method"))
                # if order.reservation_needed and not order.production_date:
                #     missing_fields.append(_('Production Date'))
                if not order.commitment_date and order.order_type != 'exhibit':
                    missing_fields.append(_("Delivery Date"))
                if not order.delivery_type_id and order.order_type != 'exhibit':
                    missing_fields.append(_("Type of Car"))
                if not order.delivery_floor_id and order.order_type != 'exhibit':
                    missing_fields.append(_("Delivery Floor"))
                # if not order.is_production and order.winner_reference and not any([att.name.endswith(".drw") for att in order.order_attachment_ids]) and not order.order_type == 'exhibit':
                #    missing_fields.append(_("Attachment (Winner .drw file)"))
                # if not order.visma_project or order.visma_project < 100:
                #     missing_fields.append(_("Angi et gyldig prosjektnummer"))
                if order.eno and order.company_id.id == Company.StraiKjokkenKristiansand.value and not order.external_sales_order_no:
                    missing_fields.append(_("Oppgi SO i Clockwork når du bestiller ENO"))
                if order.is_production:
                    so_test = re.search('^SO\d{7}$', order.external_sales_order_no if order.external_sales_order_no else '', re.IGNORECASE)
                    if not so_test:
                        missing_fields.append(_("Oppgi SO nr i Clockwork før bekreftelse av salgsordre"))
                if not order.is_production and not order.user_id:
                    missing_fields.append(_("Du må angi hvem selger er før bekreftelse av salgsordre"))
                if (order.winner_file_new_version_required or not order.is_production and order.winner_last_updated and order.winner_last_updated <= datetime(2023, 5, 2, 10, 0)) or (order.is_production and order.winner_production_last_updated and order.winner_production_last_updated <= datetime(2023, 5, 2, 10, 0)):
                    missing_fields.append(_("Du må oppdatere Winnerfila. Vennligst eksporter på nytt"))
                if not order.is_production and not order.winner_reference and not order.sale_to_self and order.order_type != 'exhibit':  # should be allowed to sell exhibition products directly from Odoo if nothing to purchase
                    missing_fields.append(_('Du kan ikke lage manuelle salgsordre i butikken. Alle bestillinger må lages i Winner og eksporteres til Odoo'))
                # Incoterm is named Delivery Method in validationError for translation purposes
                if missing_fields:
                    raise ValidationError(_("Følgende felt er ugyldig eller mangler verdi:\n%s") % "\n".join(missing_fields))

            # mark_as_delivered = order.order_type == 'exhibit' and not order.sale_to_self
            unacceptable_catalogues = []
            unacceptable_catalogues_errormsgs = []
            for line in order.order_line:
                line.sequence = seq_count
                seq_count += 1
                if line.no_supplier_warning:
                    raise UserError(_('Order %s has one or several lines with no supplier. Can not confirm before all suppliers are set.', order.name))
                if line.winner_catalogue_id and not line.winner_catalogue_id.accepted and line.winner_catalogue_id.name not in unacceptable_catalogues:
                    accepted_catalogue = self.env['winner.catalogue'].search([('supplier_id', '=', line.winner_catalogue_id.supplier_id.id), ('catalogue_name', '=', line.winner_catalogue_id.catalogue_name), ('accepted', '=', True)], order='catalogue_version asc', limit=1)
                    unacceptable_catalogues += [line.winner_catalogue_id.name]
                    unacceptable_catalogues_errormsgs += [f'UTGÅTT {line.winner_catalogue_id.name} - GJELDENDE {accepted_catalogue.catalogue_name} {accepted_catalogue.catalogue_version} {accepted_catalogue.supplier_id.name}']
                # if mark_as_delivered:
                # line.qty_delivered = line.product_uom_qty

            if unacceptable_catalogues:
                raise UserError(_('Ordren kan ikke bekreftes fordi den inneholder produkter fra utdaterte kataloger.\nLast ned siste katalog, oppdater Winner og eksporter på nytt til Odoo.\n%s' % '\n'.join(unacceptable_catalogues_errormsgs)))

            if order.external_sales_order_no:
                order.external_sales_order_no = order.external_sales_order_no.upper()
            # self._confirm_in_store() #Let it be set when order confirmation received instead
            order.timestamp_confirmed = fields.datetime.now()

            if order.is_production and not order.store_name:
                order.store_name = order.partner_id.name  # set store name to customer name if blank

            if order.order_type == 'exhibit':
                if len(order.order_line) == 0:
                    raise UserError('Minst ett produkt må velges når man selger fra utstilling.')
                if not order.is_production and order.winner_reference:
                    correct_exh_partner = self.env['res.partner'].search([('parent_id', '=', order.company_id.partner_id.id), ('name', '=', 'UTSTILLING'), ('ref', '!=', False)])
                    if not correct_exh_partner:
                        raise UserError('Korrekt utstillingspartner ikke funnet. Sjekk med systemansvarlig')
                    if order.partner_id != correct_exh_partner:
                        raise UserError(_('Butikkens kundenummer i Winner for bestilling av utstilling %s er ikke benyttet.Vennligst kansellerer dette tilbudet, og eksporter nytt tilbud fra Winner med riktig kundenummer.', correct_exh_partner.ref))

            contains_bakvegg = False
            contains_led_strip_text = False
            if len(order.order_attachment_ids) == 0 and not order.is_production:
                for line in order.order_line:
                    if 'Bakvegg' in line.name:
                        contains_bakvegg = True
                    if 'LED-strip innfrest i hylleplater' in line.name:
                        contains_led_strip_text = True
                if contains_bakvegg and not contains_led_strip_text:
                    raise UserError('Vennligst last opp nødvendige skjema:\n- Bakvegg')
                elif not contains_bakvegg and contains_led_strip_text:
                    raise UserError('Vennligst last opp nødvendige skjema:\n- LED strip')
                elif contains_bakvegg and contains_led_strip_text:
                    raise UserError('Vennligst last opp nødvendige skjema:\n- LED strip \n- Bakvegg')

            if not order.is_production and (order.user_id.name == 'Trunk' or not order.user_id):
                raise UserError('Vennligst oppgi selger.')

        return super(SaleOrder, self)._action_confirm()

    def action_sign(self):
        """ Extension to method for the 'Sign' button on the sale order. From sale_order_signed module.
            Add fields to error message if not filed
        """
        args = []
        if not self.product_type_id:
            args.append(_("Product Type"))
        # if self.reservation_needed and not self.production_date:
        #     args.append(_('Production Date'))
        if not self.commitment_date:
            args.append(_("Delivery Date"))
        missing_fields = self.sign_validation_fields(*args)
        if missing_fields:
            raise ValidationError(_("The following fields are not filled or have invalid values:\n%s") % "\n".join(missing_fields))

        if self.state in ['draft', 'sent']:
            self.state = 'signed'
            self.date_signed = fields.date.today()

    def sign_validation_fields(self, *args):
        missing_fields = []
        for field in args:
            missing_fields.append(field)

        for order in self:
            if not order.order_type:
                if len(missing_fields) > 1:
                    missing_fields.insert(1, (_('Order Type')))
                else:
                    missing_fields.append(_('Order Type'))
        return missing_fields

    # Insert comment from project into sale order onchange sales_project_id
    @api.onchange('sales_project_id')
    def get_project_comment(self):
        if self.sales_project_id:
            project = self.env['sales.projects'].search([('id', '=', self.sales_project_id.id)])
            self.update({
                'info_accounting': project.price_deal
            })
        else:
            self.info_accounting = False

    # Set analytic account for sale order when changing apartment
    @api.onchange('apartment_id')
    def get_analytic_account(self):
        if not self.is_production:
            if not self.is_production:
                if self.apartment_id:
                    self.analytic_account_id = self.apartment_id.analytic_account_id
                    self.opportunity_id.analytic_account_id.active = False
                else:
                    self.analytic_account_id = self.opportunity_id.analytic_account_id
                    self.opportunity_id.analytic_account_id.active = True

    # # Remove clear sales_project_id when changing order_type
    # @api.onchange('order_type')
    # def oncahge_order_type_remove_project(self):
    #     if self.order_type != 'project':
    #         self.sales_project_id = False
    #         self.apartment_id = False

    # Replace the above with the below
    @api.onchange('order_type')
    def onchange_order_type_clear_fields(self):
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

    # will only handle the visual effects if the user has entered a CW SO and saved, and then changes the order type
    # the readonly attribute on the view resets the value to the existing value after updating
    # if the user just switches back and forth without saving in between, it should work fine
    @api.onchange('order_type')
    def onchange_order_type_remove_external_sales_order_no(self):
        if self.order_type != 'project' and not self.is_production:
            self.external_sales_order_no = False


    # Change pricelist according to project developer pricelist.
    @api.onchange('sales_project_id')
    def _change_pricelist_for_project(self):
        for order in self:
            if order.sales_project_id and order.sales_project_id.developer_id.property_product_pricelist:
                order.pricelist_id = order.sales_project_id.developer_id.property_product_pricelist

    @api.onchange('order_type', 'builder_partner_id')
    def onchange_order_type_builder_partner_set_invoice_remark(self):
        if self.order_type == 'builder' and self.builder_partner_id and self.builder_partner_id.external_customer_identifier:
            self.remarks = self.builder_partner_id.external_customer_identifier

    # order_type campaign is handled in def price_campaing_id()
    # order_type builder is handled in def get_campaign_comment()
    @api.onchange('order_type')
    def _change_pricelist_order_type(self):
        for order in self:
            if order.order_type == 'standard':
                order.pricelist_id = order.partner_id.property_product_pricelist
            if order.order_type == 'exhibit':
                if order.is_production == True:
                    exhibit_pricelist = self.env['product.pricelist'].search([('order_type', '=', 'exhibit')])
                    order.pricelist_id = exhibit_pricelist
                else:
                    order.pricelist_id = order.partner_id.property_product_pricelist
            if order.order_type != 'builder':  # Reset builder if changing to another order type
                order.builder_partner_id = False

    @api.onchange('builder_partner_id')
    def _change_pricelist_builder(self):
        for order in self:
            if order.is_production and order.order_type == 'builder' and order.builder_partner_id:
                order.pricelist_id = order.builder_partner_id.internal_pricelist_id

    @api.onchange('price_campaign_id')
    def get_campaign_comment(self):
        campaign = self.env['strai.campaign'].search([('id', '=', self.price_campaign_id.id)])
        self.update({
            'info_accounting': campaign.campaign_info,
        })
        if self.is_production:
            if self.price_campaign_id:
                self.pricelist_id = campaign.campaign_pricelist_id

# Handled in above onchange function
    # @api.onchange('order_type')
    # def _change_builder_agreement_situation(self):
    #     for order in self:
    #         if order.order_type != 'builder':
    #             order.builder_agreement_situation = False

    @api.onchange('order_type')
    def _onchange_for_exhibit_eval(self):
        for order in self:
            if order.order_type == 'exhibit' and not order.is_production and order.winner_reference:
                correct_exh_partner = self.env['res.partner'].search([('parent_id', '=', order.company_id.partner_id.id), ('name','=','UTSTILLING'), ('ref', '!=', False)], limit=1)
                if not correct_exh_partner:
                    raise UserError('Korrekt utstillingspartner ikke funnet. Sjekk med systemansvarlig')
                if order.partner_id != correct_exh_partner:
                    raise UserError(_('Butikkens kundenummer i Winner for bestilling av utstilling %s er ikke benyttet.Vennligst kansellerer dette tilbudet, og eksporter nytt tilbud fra Winner med riktig kundenummer.', correct_exh_partner.ref))

    def write(self, values):
        res = super().write(values)
        if 'pricelist_id' in values:
            self.action_update_prices()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Check if sale order is created in the production company. If not, skip pricelist logic.
            company_id = self.env['res.company'].search([('id', '=', vals['company_id'])])
            if company_id.production:
                company = self.env['res.company']._find_company_from_partner(vals['partner_id'])
                # When created by intercompany
                if company:
                    if vals.get('order_type') in ['project', 'exhibit', 'standard']:
                        pricelist = self.env['product.pricelist'].search([('order_type', '=', vals['order_type'])])
                        if pricelist:
                            vals.update({
                                'pricelist_id': pricelist.id
                            })
                    elif vals.get('order_type') == 'builder' and vals.get('builder_partner_id'):
                        vals.update({
                            'pricelist_id': self.env['res.partner'].browse(
                                vals.get('builder_partner_id')).internal_pricelist_id.id
                        })
                    elif vals.get('order_type') == 'campaign' and vals.get('price_campaign_id'):
                        vals.update({
                            'pricelist_id': self.env['strai.campaign'].browse(
                                vals.get('price_campaign_id')).campaign_pricelist_id.id
                        })
                if vals.get('partner_shipping_id') and type(vals.get('partner_shipping_id')) != int:
                    vals['partner_shipping_id'] = vals['partner_shipping_id'].id

        res = super().create(vals_list)
        # update order_attachment_id field when SO genereate from intercompany
        for order in res:
            attachment_datas = []
            for attachment in order.auto_purchase_order_id.order_attachment_ids:
                attachment_datas.append({
                    'name': attachment.name,
                    'datas': attachment.datas,
                    'res_model': 'sale.order',
                    'res_id': order.id,
                    'is_drag_attachment': False,
                    'is_sale_attachment': True,
                })
            if attachment_datas:
                attachment_ids = self.env['ir.attachment'].create(attachment_datas)
                order.update({'order_attachment_ids': attachment_ids})
            order.update({'partner_invoice_id': order.partner_id.id})

            # add to Trunk queue, so Trunk will be notified that there is a new order in production
            # Trunk uses this information to create RPA jobs against Winner
            if company_id.production and (order.winner_reference or order.winner_reference_production):
                self.env['trunk.queue'].create_queue_item(TaskType.new_sale_order_production, self._name, order.id, order.name)
        return res

    def copy(self, default=None):
        if self.winner_reference:
            raise UserError(_("Error! You cannot copy a sale order if a Winner reference is set"))
        if self.order_type == 'exhibit':
            raise UserError(_("Error! You cannot copy a sale order if order type is 'Exhibit'"))
        return super(SaleOrder, self).copy(default)

    def create_sale_orders(self, data):
        """ Used for creating sale order through the trunk
        :param list data : list of dictionaries containing order information
        """
        orders = []
        for order in data['orders']:
            # Process
            orders.append(self.with_company(order['sales_company']).create_sale_order(order))
        return orders

    def get_ir_default_value(self,value):
        model_name = 'sale.order'
        uid = value.get('user_id') if value.get('user_id') else 0
        company = value.get('company_id') if value.get('company_id') else 0
        condition = False
        cr = self.env.cr
        query = """ SELECT f.name, d.json_value
                    FROM ir_default d
                    JOIN ir_model_fields f ON d.field_id=f.id
                    WHERE f.model=%s
                        AND (d.user_id IS NULL OR d.user_id=%s)
                        AND (d.company_id IS NULL OR d.company_id=%s)
                        AND {}
                    ORDER BY d.user_id, d.company_id, d.id
                """
        # self.env.company is empty when there is no user (controllers with auth=None)
        params = [model_name, uid, company or None]
        if condition:
            query = query.format("d.condition=%s")
            params.append(condition)
        else:
            query = query.format("d.condition IS NULL")
        cr.execute(query, params)
        result = {}
        for row in cr.fetchall():
            # keep the highest priority default for each field
            if row[0] not in result:
                result[row[0]] = json.loads(row[1])
        for key,val in result.items():
            if not value.get(key):
                value.update({key:val})
        return value

    def create_sale_order(self, order_data):
        """ Creates a single sale order from a dictionary of information. See required information in trunk_endpoint_sale/documentation/order
        Supplierinfo and routes are always updated.
        If sale order exists and its state is not in draft or sale, we update it, delete all order lines, and insert order lines from arg order_data
        If sale order does not exist, we create it with values from arg order_data
        :param dict order_data : Information about the order and lines
        :return integer : id of new or exisiting sale order
        :
        """
        production_company = self.env['res.company'].search([('production', '=', True)])
        # shop version of winnerfile
        if order_data.get('order_version') == False:
            order = self.search(['&', ('winner_reference', '=', order_data['winner_reference']), ('company_id', '=', order_data['sales_company'])])
        # order version of winnerfile
        elif order_data.get('order_version') == True:
            order = self.sudo().search(['&', ('winner_reference_production', '=', order_data['winner_reference']), ('company_id', '=', production_company.id), ('state', '!=', 'cancel')], limit=1)
        else:
            raise AttributeError("Could not read if this is an order version or not")

        sale_to_self = self._check_company_customer(order_data['customer']['winner_customer_id'])

        if order and order_data.get('order_version'):
            # We have a winner reference from Winner
            # Check if we can find an existing sale order that match the reference in the production company.
            # If so - overwrite it with the new data but don't change the original sale order
            values = self._prepare_values(order_data, production_company, winner_ref_match=True, sale_to_self=sale_to_self)
            if order.state != 'sale' and 'pricelist_id' not in values:
                values['pricelist_id'] = order.pricelist_id.id
            order.sudo().write(values)

        if not order:
            values = self._prepare_values(order_data, production_company, sale_to_self=sale_to_self)
            # If company and customer is the same (If the store are buying an exhibition kitchen for example)
            if sale_to_self:
                values['order_type'] = 'exhibit'
                
            values = self.get_ir_default_value(values)
            order = self.env['sale.order'].create(values)

        # do not update order in shop when it is completed
        if order and not order.is_production and order.state in ['sale', 'done', 'cancel']:
            return order.name

        if order and order.state in ['draft', 'sent', 'signed', 'reserved']:
            order.sale_to_self = sale_to_self
            order.winner_file_new_version_required = False
            order.tag_ids = self.get_tag_ids(order_data)
            if not order.company_id == production_company or not order.winner_reference:
                order_data['customer']['update'] = True
                # don't think this is used?
                # order_data['customer']['update_partner'] = order.partner_shipping_id
                # Add shipping address to handle multiple addresses
                # if not order.partner_id.independent_shop:
                order.winner_file_id = order_data.get('winnerfile_id')
                if not sale_to_self:
                    order.partner_id = self.env['res.partner'].create_contact(order_data['customer'], 'contact')

                    # always set invoice_partner_id to partner_id
                    # order.partner_invoice_id = self.env['res.partner'].create_contact(order_data['customer_invoice'], 'invoice')
                    order.partner_invoice_id = order.partner_id
                    order.partner_shipping_id = self.env['res.partner'].create_contact(order_data['customer_shipping'], 'delivery')
                else:
                    partner_id = sale_to_self.id
                    order.partner_id = partner_id
                    order.partner_invoice_id = partner_id
                    order.partner_shipping_id = partner_id
            if order_data.get('order_lines'):
                advance_product = order.company_id.sale_down_payment_product_id.id
                order.order_line.filtered(lambda o: o.product_id.id != advance_product and not (o.name == "Forskuddsbetaling" and o.display_type == 'line_section')).unlink()
                for line in order_data['order_lines']:
                    self._create_sale_order_line(order, order_data.get('order_version'), line)
        else:
            self._handle_order_corrections(order, order_data)

        # keep existing pricelist if intercompany SO
        pricelist_id = order.pricelist_id
        if not order_data.get('order_version'):
            order.user_id = self.env['res.users'].search([('phone', '=', order_data['sales_phone'])], limit=1).id or order.user_id
        elif order.user_id.id == ResUser.Trunk.value:
            order.user_id = False
        if not order.payment_term_id:
            std_payment_term = order.company_id.default_payment_term
            if std_payment_term:
                order.payment_term_id = std_payment_term
            else:
                order.payment_term_id = PaymentTerm.Days30.value
        if not order.delivery_floor_id:
            order.delivery_floor_id = DeliveryFloor.Zero.value
        if not order.delivery_type_id:
            order.delivery_type_id = DeliveryType.Regular.value
        if not order.delivery_method_id:
            order.delivery_method_id = DeliveryMethod.DeliverToCustomer.value
        order.action_update_taxes()
        current_user_mail = self.env.user.email
        self.remove_as_follower(order, current_user_mail)
        self.check_roundoff(order, order_data)
        if pricelist_id and order_data.get('order_version'):
            order.pricelist_id = pricelist_id
            order.with_company(production_company).action_update_prices()
            #order.action_update_prices()
        if order_data.get('order_version'):
            order.winner_production_last_updated = datetime.now()
        else:
            order.winner_last_updated = datetime.now()
            # phone numbers
            order.delivery_phone_one = order_data.get('customer', {}).get('mobile', False) or False
            order.delivery_phone_two = order_data.get('customer', {}).get('phone', False) or False
        return order.name

    # create sale order line from Winner
    def _create_sale_order_line(self, order, order_version, order_line):
        if not (order_version == True and order_line.get('direct_supplier')):
            if order_line.get('line_type') in [2, 3]:
                self.env['sale.order.line'].sudo().create({
                    'name': order_line['product']['name'],
                    'position': order_line['item_position'],
                    'display_type': 'line_note' if order_line['line_type'] == 2 else 'line_section',
                    'order_id': order.id,
                })
            else:
                product_id = self.env['product.product'].create_product(order_line['product'], order.company_id)
                self.env['sale.order.line'].sudo().create(self._prepare_line_values(order_line, order, product_id, order_version))

    def _handle_order_corrections(self, order, order_data):
        # handle order corrections after confirmation / partial confirmation
        if order_data.get('order_version') and order.state == 'sale' and order_data.get('order_lines'):
            ir_config_parameter = self.env['ir.config_parameter'].sudo()
            # advance_product = int(ir_config_parameter.get_param('sale.default_deposit_product_id'))
            advance_product = order.company_id.sale_down_payment_product_id.id

            # check for deleted lines
            deleted_sols = [sol for sol in order.order_line if sol.position not in [ol['item_position'] for ol in order_data['order_lines']] and sol.position != 0 and sol.product_uom_qty > 0.0]

            # check for new lines
            new_orderlines = []
            # new_orderlines = [ol for ol in order_data['order_lines'] if ol['item_position'] not in [sol.position for sol in order.order_line]]

            # check for changed lines
            for line in order_data['order_lines']:
                sol = order.order_line.filtered(lambda l: l.position == line['item_position'])

                # typical for position = 0, no real match. No actions
                if sol and (len(sol) > 1 or sol.position == 0 or sol.display_type in ['line_note', 'line_section']):
                    continue

                # check for new line
                if not sol or sol.product_uom_qty == 0.0:
                    new_orderlines.append(line)
                    continue


                product_id = self.env['product.product'].create_product(line['product'], order.company_id)

                # check for changed product on same position
                if sol.product_id.id != product_id:
                    deleted_sols.append(sol)
                    new_orderlines.append(line)
                    continue

                product = self.env['product.product'].with_company(order_data['sales_company']).search([('id', '=', product_id)])
                new_vendor = sol.current_vendor.id if sol.current_vendor else False
                if product and len(product.seller_ids) > 0:
                    for vendor in product.with_company(self.env.company.id).seller_ids:
                        if vendor.company_id.id == order_data['sales_company']:
                            new_vendor = vendor.id
                            break
                        else:
                            new_vendor = False

                # get purchase order and purchase order line
                po = False
                pol = False
                if sol.current_vendor.partner_id:
                    po = self.env['purchase.order'].search(['&', ('origin', '=', order.name), ('partner_id', '=', sol.current_vendor.partner_id.id)])
                    pol = [pol for pol in po.order_line if pol.position == line['item_position']]
                    if len(pol) > 0:
                        pol = pol[0]

                # check for missing supplier from previous import - OK to use current in this case
                if not sol.current_vendor and new_vendor:
                    sol.current_vendor = new_vendor
                # check for changed supplier
                elif sol.current_vendor.id != new_vendor and new_vendor:
                    if po:
                        # original pol no longer valid. Set qty to 0 and create warning
                        if pol:
                            pol.product_uom_qty = 0.0
                        deleted_sols.append(line)
                        new_orderlines.append(line)

                        if po.state in ['purchase', 'done']:
                            # generate warning activity on purchase order
                            self.env['mail.activity'].sudo().create({
                                'res_model': 'purchase.order',
                                'res_model_id': self.env['ir.model'].search([('model', '=', 'purchase.order')]).id,
                                'user_id': po.user_id.id,
                                'res_id': po.id,
                                'activity_type_id': self.env['mail.activity.type'].search([('id', '=', ActivityType.ChangedAfterConfirmation)]).id,
                                'summary': _(f'Order line has different vendor than Winner ({sol.position}) {sol.current_vendor.partner_id.name} | {new_vendor.partner_id.name}'),
                            })
                    else:
                        # change the line directly, PO has not been created yet
                        sol.current_vendor = new_vendor

                # check for updated description
                if sol.name != line['product']['name']:
                    # update sol and pol
                    sol.name = line['product']['name']
                    # pol.description = line['product']['name']
                # check for updated price unit, generate warnings on purchase order as necessary
                if sol.price_unit != line['product']['catalogue_price']:
                    sol.price_unit = line['product']['catalogue_price']
                    # pol.price_unit = line['product']['sale_price']
                # check for updated price unit, generate warnings on purchase order as necessary
                if sol.catalogue_price != line['product']['catalogue_price']:
                    sol.catalogue_price = line['product']['catalogue_price']
                    # pol.catalogue_price = line['product']['catalogue_price']
                # check for changed qty
                if sol.product_uom_qty != line['quantity']:
                    # warnings should be generated based on this changed value in onchange function, to be applied also on changes from ui
                    sol.product_uom_qty = line['quantity']

            # set qty = 0 on deleted sols
            for deleted_sol in deleted_sols:
                if deleted_sol.product_id.id != advance_product and not (deleted_sol.name == "Forskuddsbetaling" and deleted_sol.display_type == 'line_section'):
                    deleted_sol.product_uom_qty = 0.0

            # create new sols
            for new_orderline in new_orderlines:
                self._create_sale_order_line(order, order_data.get('order_version'), new_orderline)

    def check_roundoff(self, order, order_data):
        # only use roundoff in shops
        if order.is_production:
            return

        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        default_round_off_product = ir_config_parameter.get_param('strai.round_off_product')
        roundoff_product = self.env['product.product'].browse(int(default_round_off_product))
        if not default_round_off_product:
            raise UserError(_("A default Roundoff Product is not set. Go to settings(In applications) --> General Settings --> Trunk"))
        quotation_total_price = order_data.get('quotation_total_price')
        quotation_diff = order.amount_total - float(quotation_total_price)
        if quotation_diff < 0.0:
            quotation_diff = quotation_diff * -1
            qty = 1
        else:
            qty = -1
        roundoff_completed = False
        for line in order.order_line:
            if line.product_id.id == roundoff_product.id:
                line.price_unit = quotation_diff
                line.product_uom_qty = qty
                roundoff_completed = True
                break

        if not roundoff_completed:
            if quotation_total_price and quotation_diff != 0:
                # If the difference in price between the sale order total and the real total from the trunk is a
                # posstive number, convert the difference to a negative number and add it as a sale order line to
                # round off.

                tax_id_5_zero = self.env['account.tax'].sudo().search([('company_id', '=', order.company_id.id), ('name', 'ilike', '5 Mvafritt%')], limit=1)

                # add order section before rounding product
                self.env['sale.order.line'].sudo().create({
                    'name': 'Avrunding',
                    'display_type': 'line_section',
                    'order_id': order.id
                })

                self.env['sale.order.line'].sudo().create({
                    'product_id': roundoff_product.id,
                    'product_uom_qty': qty * -1 if quotation_diff < 0.0 else qty,
                    'order_id': order.id,
                    'name': roundoff_product.with_context(lang=order.partner_id.lang).get_product_multiline_description_sale(),
                    'price_unit': quotation_diff * -1 if quotation_diff < 0.0 else quotation_diff,
                    'tax_id': tax_id_5_zero if tax_id_5_zero else False,
                })

    def _prepare_line_values(self, line_data, order, product_id, order_version):
        vendor_id = False
        product_id_id = self.env['product.product'].with_context(active_test=False).search([('id', '=', product_id)])
        production_product = self.env['product.product'].with_context(active_test=False).is_production_product(line_data['product'])
        if (line_data.get('product', {}).get('direct_supplier', False) or order.company_id.production) and not production_product:
            vendor_id = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product_id_id.product_tmpl_id[0].id), ('partner_id.ref', '!=', 1000), ('winner_product_code', '=', line_data['product']['reference']), ('company_id', '=', order.company_id.id)])
        else:
            if not (production_product and order.company_id.production):
                vendor_id = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product_id_id.product_tmpl_id[0].id), ('winner_product_code', '=', line_data['product']['reference']), ('partner_id.ref', '=', 1000), ('company_id', '=', order.company_id.id)])
        if line_data['product']['supplier_code']:
            supplier = self.env['res.partner'].search([('ref', '=', line_data['product']['supplier_code'])], limit=1)
        else:
            supplier = False
        winner_catalogue = self.get_winner_catalogue(supplier.id if supplier else False, line_data['product']['catalogue_name'], line_data['product']['catalogue_version'])
        return {
            'product_id': product_id,
            'product_uom_qty': line_data.get('quantity'),
            'order_id': order.id,
            'position': line_data.get('item_position'),
            'name': line_data['product']['name'],
            'price_unit': line_data['product']['catalogue_price'] if order_version else line_data['product']['sale_price'],
            'discount': self.calculate_discount(line_data['product'], line_data),
            'current_vendor': vendor_id[0].id if vendor_id else False,
            'catalogue_price': line_data['product']['catalogue_price'],
            'winner_catalogue_id': winner_catalogue.id if winner_catalogue else False
        }

    def get_winner_catalogue(self, supplier_id, catalogue_name, catalogue_version):
        if not supplier_id or not catalogue_name or not catalogue_version:
            return False
        winner_catalogue = self.env['winner.catalogue'].search([('supplier_id', '=', supplier_id), ('catalogue_name', '=', catalogue_name), ('catalogue_version', '=', catalogue_version)])
        if not winner_catalogue:
            # if other versions of the same catalogue exists, and some are already deactivated, also deactivate this one if version is lower than the deactivated one
            winner_catalogue_other_version = self.env['winner.catalogue'].search([('supplier_id', '=', supplier_id), ('catalogue_name', '=', catalogue_name), ('accepted', '=', False)], order='catalogue_version desc', limit=1)
            accepted = True
            if winner_catalogue_other_version and winner_catalogue_other_version.catalogue_version >= catalogue_version:
                accepted = False
            winner_catalogue = self.env['winner.catalogue'].create({
                'name': f'{catalogue_name}{catalogue_version}',
                'supplier_id': supplier_id,
                'catalogue_name': catalogue_name,
                'catalogue_version': catalogue_version,
                'accepted': accepted
            })
        return winner_catalogue

    def calculate_discount(self, product, line):
        if product.get('sale_price') and product.get('total_price'):
            tax = 1.25
            # failsafe for zero division
            if product['sale_price'] == 0.0 or line.get('quantity', 0.0) == 0.0:
                return 0.0
            return (1 - product['total_price'] / (product['sale_price'] * line.get('quantity', 0.0) * tax)) * 100
        return 0.0

    def _prepare_write_values(self, line_data):
        return {
            'price_unit': line_data['product']['sale_price'],
        }

    def _prepare_values(self, order_data, production_company, winner_ref_match=False, sale_to_self=False):
        values = {}
        res_partner = self.env['res.partner']
        crm_lead = self.env['crm.lead'].with_company(order_data['sales_company'])
        # Required
        if order_data.get('order_version') == False:
            user_id = self.env['res.users'].search([('phone', '=', order_data['sales_phone'])]).id
            values['user_id'] = user_id or values.get('user_id') or False
            values['company_id'] = self.env['res.company'].browse(order_data['sales_company']).id
            values['winner_reference'] = order_data.get('winner_reference')
        # If order_version == True. The sale order should be created in strai production.
        else:
            values['company_id'] = production_company.id
            values['winner_reference_production'] = order_data.get('winner_reference')
        if not winner_ref_match:
            if sale_to_self:
                values['partner_id'] = sale_to_self.id
            else:
                values['partner_id'] = res_partner.create_contact(order_data['customer'], 'contact')
            # change pricelist automatically based on customer number from Winner
            if order_data['customer']['reference'].startswith('1/'):
                winner_customer = self.env['winner.customer'].search([('customer_number', '=', order_data['customer']['reference'][2:])], limit=1)
                if winner_customer and (values.get('pricelist_id') == 1 or not values.get('pricelist_id')):
                    values['pricelist_id'] = winner_customer.pricelist_id.id
            if 'winner_lead_ref' in order_data:
                # We have a CRM reference from Winner
                # Check if we can find an existing lead
                # Otherwise create a new one
                if values.get('user_id'):  # if no user ID, defaulting to "manual order" - new CRM lead with no Winner lead ref
                    values['opportunity_id'] = crm_lead._create_lead(order_data, self.env['res.partner'].browse(values['partner_id']), values['user_id'])

            # always set partner_invoice_id to partner_id
            # if order_data.get('customer_invoice'):
            #     values['partner_invoice_id'] = res_partner.create_contact(order_data['customer_invoice'], 'invoice')

            values['partner_invoice_id'] = values['partner_id']

            if sale_to_self:
                values['partner_shipping_id'] = sale_to_self.id
            elif order_data.get('customer_shipping'):
                values['partner_shipping_id'] = res_partner.create_contact(order_data['customer_shipping'], 'delivery')
        # Optional
        values['client_ref'] = order_data.get('customer_reference')
        values['origin'] = order_data.get('order_number')
        # values['winner_reference'] = order_data.get('winner_reference')
        values['winner_file_id'] = order_data.get('winnerfile_id')
        # values['external_sales_order_no'] = order_data.get('external_sales_order_number')
        if order_data.get('tags'):
            values['tag_ids'] = self.get_tag_ids(order_data)

        if sale_to_self:
            values['sale_to_self'] = True
        return values

    def get_tag_ids(self, order_data):
        trunk_tags = [t_tag.capitalize() for t_tag in order_data['tags']]
        odoo_tags = self.env['crm.tag'].search([('name', 'in', trunk_tags)])

        tags_to_create = list(set(trunk_tags) - set(odoo_tags.mapped('name')))
        tag_ids = [self.env['crm.tag'].sudo().create({'name': t}).id for t in
                   tags_to_create] if tags_to_create else []
        tag_ids.extend(odoo_tags.ids)

        return tag_ids

    def mark_as_delivered(self, order_data):
        """ Marks sale orders as delivered. Allowing a CRON job to fulfil the orders automatically (module: validate_deliveries)
        :param list order_data : list of sale order names
        :return list : ids of orders that has been marked as delivered by the trunk
        :
        """
        orders = []
        for order in order_data['orders']:
            orders.append(self._mark_as_delivered(order))
        return orders

    def _mark_as_delivered(self, order):
        order = self.sudo().search([('name', '=', order['order_name'])])
        if order:
            order.delivery_confirmed = True
            return order.name

    def remove_as_follower(self, order, email):
        for follower in order.message_follower_ids:
            if follower.partner_id.email == email:
                follower.sudo().unlink()

    def change_date_planned(self, order_data):
        """Change date on dict of orders
        :param dict order_data : dict of sale order names and dates
        :return list : ids of orders that has been changed
        :
        """
        orders = []
        for order in order_data['orders']:
            orders.append(self._change_date_planned(order))
        return orders

    def _change_date_planned(self, order):
        order = self.sudo().search([('name', '=', order['order_name'])])
        if order:
            order.date_planned = order['commitment_date']
            return order

    # Check if customer and sale company is actually the same
    def _check_company_customer(self, customer_id):
        partner_id = self.env['res.partner'].search([('ref', '=', customer_id), ('parent_id', '!=', False)], limit=1)
        partner_company = self.env['res.company'].find_company_from_partner(partner_id.parent_id) or False
        if partner_company:
            return partner_id
        return False

    def open_winner_wizard(self):
        self.get_winner_vals()
        wizard = self.env['winner.ref.wizard'].create(self.get_winner_vals())
        return {
            'name': _('Winner Ref Wizard'),
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'winner.ref.wizard',
            'res_id': wizard.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def get_winner_vals(self):
        if self.winner_reference and len(self.winner_reference) > 2:
            winner_reference = self.winner_reference
            environment = (winner_reference.rsplit('/', 1)[0].rsplit('/', 1)[1])
            alt = winner_reference.rsplit("/", 1)[1]
        else:
            raise UserError(_('There is no winner reference to edit'))
        return {'sale_order': self.id,
                'winner_reference': winner_reference,
                'alternative': alt,
                'environment': environment}

    # Capacity logic
    @api.depends('order_line')
    def _compute_reservation_needed(self):
        for order in self:
            if order.calculate_sectionscount() < 1:
                order.reservation_needed = False
            else:
                order.reservation_needed = True

    reservation_needed = fields.Boolean(compute=_compute_reservation_needed)

    def _get_capacity_category(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        category = ir_config_parameter.get_param('strai.capacity_booking_product_category')
        return int(category)

    def action_capacity(self):
        for order in self:
            if order.state in ['signed', 'sale']:
                order.check_product_category()
                # check that a sales person is set
                if not order.user_id:
                    raise UserError(_('Assign a sales person before reservation'))
                # check if reservation date is before confirmation deadline
                if order.capacity_booking_deadline < datetime.now().date():
                    raise UserError(_('You can not reserve an order earlier than the order deadline'))
                if order.production_date:
                    order.book_capacity()
                    order.is_confirmed = True
                    order.state = 'reserved'
                else:
                    raise UserError(_('Please choose a delivery date before calculating manufacturing capacity'))
            else:
                raise UserError(_('This order is not yet signed. It has to be signed to make a booking in the production'))

    def action_no_capacity(self):
        raise UserError(_("There is no capacity for the choosen delivery date. Contact the customer center to solve the issue."))

    # Calculate week number from datetime object
    def week_number(self, start_date):
        # You can add delay to this function, so that you check for capacity before the delivery date (currently handled by winner).
        # The 7 days is the +1 week in the buttom of this function.
        new_date = (datetime.strptime(str(start_date), "%Y-%m-%d %H:%M:%S") + relativedelta(days=- 7))
        d = time.strptime(str(new_date), "%Y-%m-%d %H:%M:%S")
        week_number = strftime("%W", d)
        return int(week_number) + 1

    # Reserve capacity via trunk API
    def book_capacity(self):
        for order in self:
            project_name_data = order.get_project_names(order)
            # new booking
            if order.state == 'signed' and not order.product_type_id:
                raise UserError(_("The field 'Product Type' is mandatory"))
            payload = {"WinnerfileId": int(order.winner_file_id),
                       "OdooId": order.id,
                       "DeliveryDate": str(fields.Date.context_today(order, order.commitment_date)),
                       "ReservedDate": str(order.capacity_booking_deadline),
                       "Zipcode": int(order.company_id.zip),
                       "SectionsCount": order.calculate_sectionscount(),
                       "CompanyName": order.company_id.name,
                       "SalesPersonName": order.user_id.name,
                       "SalesPersonEmail": order.user_id.login,
                       "Project": project_name_data['sales_project_name'],
                       "Apartment": project_name_data['apartment_name'],
                       "CustomerName": order.partner_id.name
                       }
            content = self.env['strai.trunk'].get_data_from_trunk(ENDPOINT_BOOK_CAPACITY, payload)
            if 'OrderDeadline' in content.keys():
                # deadline = content['OrderDeadline']
                # x = deadline.split('T')
                # order.capacity_booking_deadline = str(x[0])
                order.booked_by_store = True

    # Can't send datetime object through json.
    def prepare_date(self, date):
        d = datetime.strptime(str(date)[:10], "%Y-%m-%d")
        return d.date()

    def get_project_names(self, order):
        sales_project_name = ""
        apartment_name = ""
        if order.sales_project_id:
            sales_project_name = order.sales_project_id.name
        if order.apartment_id:
            apartment_name = order.apartment_id.name
        return {'sales_project_name': sales_project_name,
                'apartment_name': apartment_name}

    # When production date is changed compute capacity.
    @api.depends('commitment_date')
    def _compute_capacity(self):
        for record in self:
            if record.commitment_date:
                week = record.week_number(record.commitment_date)
                capacity = self.env['mrp.capacity.booking'].search([('delivery_year', '=', record.commitment_date.year), ('delivery_week', '=', week)], limit=1)
                if capacity.id:
                    record.capacity = capacity.capacity
                else:
                    # If there is no capacity.id it means that the booking was made more than 26 weeks in the future, which is allowed.
                    # therefore, capacity can never be false if the user entered a date
                    record.capacity = 'good'
            else:
                record.capacity = False

    @api.onchange('commitment_date')
    @api.depends('commitment_date')
    def _compute_capacity_from_date(self):
        for order in self:
            if not order.company_id.production and order.winner_file_id and order.commitment_date:
                date = order.prepare_date(fields.Date.context_today(order, order.commitment_date))
                url_args = '?winnerfileId={}&deliveryDate={}'.format(order.winner_file_id, date)
                content = self.env['strai.trunk'].get_data_from_trunk(ENDPOINT_ORDER_DEADLINE + url_args)
                if content:
                    if 'Deadline' in content.keys():
                        x = content['Deadline']
                        order.capacity_booking_deadline = datetime.strptime(str(x), "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")

                else:
                    order.capacity_booking_deadline = False

    def action_delete_reservation(self):
        for order in self:
            order._delete_reservation()
            # order.capacity_booking_deadline = ""
            order.is_confirmed = False
            if order.state == 'reserved':
                order.state = 'signed'

    def _delete_reservation(self):
        trunk = self.env['strai.trunk']
        url_arg = '?odooid={}'.format(self.id)
        response_status_code = trunk.delete_data_in_trunk(ENDPOINT_DELETE + url_arg)
        if response_status_code in [200, 201, 204]:
            self.booked_by_store = False
        else:
            _logger.error("Time slot could not be deleted")

    def action_cancel(self):
        if self.is_confirmed:
            self._delete_reservation()
            self.is_confirmed = False
        return super(SaleOrder, self).action_cancel()

    def calculate_sectionscount(self):
        capacity_category = self._get_capacity_category()
        categories = self.env['product.category'].search(['|', ('id', 'child_of', capacity_category), ('id', '=', capacity_category)])
        amount_sections = 0
        for line in self.order_line:
            if line.product_id.categ_id in categories:
                amount_sections += line.product_uom_qty
        return int(amount_sections)

    def check_product_category(self):
        for order in self:
            if not order._get_capacity_category():
                raise UserError(_("A capacity booking product category has not been set. Go to settings(in applications) -> Sales -> Capacity Booking --> Choose the product category that are going to be produced"))
            if order.calculate_sectionscount() < 1:
                raise UserError(_("There are no manufactured products on the order"))

    @api.onchange('commitment_date')
    def onchange_commitment(self):
        for order in self:
            if not order.commitment_date:
                return
            tz_commitment_date = fields.Date.context_today(order, order.commitment_date)
            if tz_commitment_date.isoweekday() in [6, 7]:
                raise UserError(_("Orders can only be sent during weekdays"))
            if tz_commitment_date in order.norwegian_holidays:
                raise UserError(_("Orders can not be sent during norwegian holidays"))
            if not order.booked_by_store:
                order.production_date = order.commitment_date - timedelta(days=3)

    def fake_button(self):
        pass

    # Fetches related PO. Note you can not trust "origin" field on the related PO, as this points to the EXTERNAL SO (-> Customer), not the INTERNAL SO (Store <-> Production)
    def get_related_po(self):
        return self.env['purchase.order'].sudo().search([('name', '=', self.client_order_ref)])

    # Creates an activity on the related PO (Store) when date is changed on the SO (Production)
    # Watches Delivery date and initates logic that updates date_planned on PO when triggered
    @api.onchange('commitment_date')
    def _check_po_commitment(self):
        for record in self:
            if record.is_production:
                related_po = self.get_related_po()
                if related_po and related_po.date_order != record.commitment_date:
                    related_po.date_planned = record.commitment_date
                    # record._notify_store(related_po)

    # Creates activity
    # def _notify_store(self, po):
    #     self.env['mail.activity'].sudo().create({
    #         'res_model': 'purchase.order',
    #         'res_model_id': self.env['ir.model'].sudo().search([('model', '=', 'purchase.order')]).id,
    #         'user_id': po.user_id.id,
    #         'res_id': po.id,
    #         'activity_type_id': self.env['mail.activity.type'].search([('id', '=', 4)]).id,
    #         'summary': _('Commitment Date on Sales Order changed by Production'),
    #     })

    # Confirms the related PO in store when SO in Production is confirmed (function below)
    def _confirm_in_store(self):
        if self.is_production:
            related_po = self.get_related_po()
            related_po.supplier_confirmed = True

    # Transfers fields to resulting Invoices
    def _prepare_invoice(self):
        vals = super(SaleOrder, self)._prepare_invoice()

        vals.update({
            'product_type_id': self.product_type_id.id,
            'order_type': self.order_type,
            'remarks': self.remarks,
            'ref': f"{self.client_order_ref} / {self.remarks}" if (self.client_order_ref and self.remarks) else (self.remarks or self.client_order_ref or ''),
            'stria_purchase_id': self.auto_purchase_order_id.id,
            'price_campaign_id': self.price_campaign_id.id,
            'strai_analytic_account_id': self.exhibit_analytic_account_id.id,
            'builder_partner_id': self.builder_partner_id.id,
            'builder_agreement_situation': self.builder_agreement_situation,
            'sales_project_id': self.sales_project_id.id,
            'apartment_id': self.apartment_id.id,
            'store_user_name': self.store_user_name,
            'warranty_selected': self.warranty_selected,
            'store_warranty_order': self.store_warranty_order,
            'winner_reference': self.winner_reference

        })
        return vals

    def _cron_update_this_day(self):
        current_date = datetime.now().date()
        self.env.cr.execute("UPDATE sale_order SET this_day = %s WHERE state in ('draft', 'sent', 'signed', 'reserved')", (current_date,))

    @staticmethod
    def _validate_delivery_address(partner_id):  # partner_id object
        valid = True
        if not partner_id.street or len(partner_id.street) < 2:
            valid = False
        elif not partner_id.zip or len(partner_id.zip) != 4:
            valid = False
        elif not partner_id.city or len(partner_id.city) < 2:
            valid = False
        return valid

    @staticmethod
    def _validate_customer_address(partner_id):
        valid = True
        if not partner_id or len(partner_id.name) < 2:
            valid = False
        return valid

    @staticmethod
    def get_fields_to_ignore_in_search():
        return ['campaign_id', 'project_id']

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(SaleOrder, self).fields_get(allfields, attributes=attributes)
        for field in self.get_fields_to_ignore_in_search():
            if res.get(field):
                res.get(field)['searchable'] = False
        return res

    def invoiced_manually(self):
        for order in self:
            order.invoice_status = 'invoiced'

    @staticmethod
    def _show_cancel_wizard():
        return False

    # override sale/models/sale_order
    @api.depends('partner_id')
    def _compute_partner_invoice_id(self):
        for order in self:
            order.partner_invoice_id = order.partner_id or False

    # override sale/models/sale_order
    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = order.partner_id or False

    @api.model
    def retrieve_sale_dashboard(self, action_id):
        result = {}
        sale_action_ids = [self.env.ref('sale.action_quotations_with_onboarding').id, self.env.ref('sale.action_orders').id]
        if self.env.company.production or action_id not in sale_action_ids:
            result['show_dashboard'] = False
            return result
        result['show_dashboard'] = True

        so = self.env['sale.order']
        if action_id == self.env.ref('sale.action_quotations_with_onboarding').id:
            result['all_draft_and_sent'] = so.search_count([('state', 'in', ['draft', 'sent'])])
            result['my_draft_and_sent'] = so.search_count([('state', 'in', ['draft', 'sent']), ('user_id', '=', self.env.uid)])

        else:
            # Sale order does not contain any draft or sent state
            result['all_draft_and_sent'] = 0
            result['my_draft_and_sent'] = 0

        # state already defined in domain
        result['all_signed_and_reserved'] = so.search_count([('state', 'in', ['signed', 'reserved'])])
        result['my_signed_and_reserved'] = so.search_count([('state', 'in', ['signed', 'reserved']), ('user_id', '=', self.env.uid)])
        result['all_sale_invoice_status_no'] = so.search_count([('state', '=', 'sale'), ('invoice_status', '=', 'no')])
        result['my_sale_invoice_status_no'] = so.search_count([('state', '=', 'sale'), ('invoice_status', '=', 'no'), ('user_id', '=', self.env.uid)])
        result['all_to_invoice'] = so.search_count([('invoice_status', '=', 'to invoice')])
        result['my_to_invoice'] = so.search_count([('invoice_status', '=', 'to invoice'), ('user_id', '=', self.env.uid)])

        return result

    # Get PO object based on the client order reference.
    def _get_purchase_order_by_ref(self):
        po_ref = self.client_order_ref
        if po_ref:
            po = self.env['purchase.order'].sudo().search([('name', '=', po_ref)], limit=1)
            if po:
                return po

        return False

    @api.depends('sales_rep_affiliated_store', 'store_responsible_id')
    def _compute_store_user_name(self):
        for order in self:
            if order.is_production:
                if order.store_responsible_id and order.is_strai_store:
                    order.store_user_name = order.store_responsible_id.name
                if order.sales_rep_affiliated_store.name and not order.is_strai_store:
                    order.store_user_name = order.sales_rep_affiliated_store.name
                if not order.sales_rep_affiliated_store and not order.store_responsible_id:
                    order.store_user_name = False

    @api.onchange('partner_id')
    @api.depends('partner_id')
    def _compute_is_strai_store(self):
        for order in self:
            partner_related_to_company = self.env['res.company'].sudo().search([('partner_id', '=', order.partner_id.id), ('name', 'ilike', 'strai')], limit=1)
            if partner_related_to_company:
                order.is_strai_store = True
            else:
                order.is_strai_store = False

    def is_business_day(self, date):
        # Check if the day is a Saturday or Sunday
        if date.weekday() >= 5:
            return False
        # Check if the day is a public holiday
        if date in self.norwegian_holidays:
            return False
        return True

    def subtract_business_days(self, date, num_days):
        current_date = date
        business_days_subtracted = 0

        while business_days_subtracted < num_days:
            current_date -= timedelta(days=1)
            if self.is_business_day(current_date):
                business_days_subtracted += 1

        return current_date
    @api.onchange('capacity_booking_deadline')
    @api.depends('capacity_booking_deadline')
    def _compute_order_change_cutoff_date(self):
        for order in self:
            if order.capacity_booking_deadline:
                order.order_change_cutoff_date = order.subtract_business_days(order.capacity_booking_deadline, 5)
