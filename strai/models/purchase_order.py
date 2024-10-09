import threading

import requests

from ..helper.res_user import ResUser
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

from ...trunk_queue.helper.trunk_queue_enum import TaskType

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    order_id = fields.Many2one('sale.order')
    purchase_id = fields.Many2one('purchase.order')

    # Info fields:
    delivery_phone_one = fields.Char()
    delivery_phone_two = fields.Char()

    info_transport = fields.Text("Transport Comment")
    info_production = fields.Text("Production Comment")
    info_accounting = fields.Text("Accounting Comment")
    info_supplier = fields.Text("Supplier Comment")

    delivery_floor_id = fields.Many2one('delivery.floor', string="Delivery Floor")

    # Delivery Type
    delivery_type_id = fields.Many2one('delivery.type', string="Delivery Type")
    delivery_method_id = fields.Many2one('delivery.method')

    # Product Type
    product_type_id = fields.Many2one('product.type', string="Product Type")
    order_attachment_ids = fields.Many2many('ir.attachment', string="Attachment")
    winner_reference = fields.Char(string="Winner")
    sale_reference = fields.Char()
    capacity_booking_deadline = fields.Date()
    store_responsible_id = fields.Many2one('res.users')
    production_date = fields.Datetime()

    visma_project = fields.Integer(required=False)
    origin_sales_order_no = fields.Char("Origin sales order no")
    winner_reference_production = fields.Char(string="Winner production", readonly=True)
    winner_file_id = fields.Char(default="1")
    winner_last_updated = fields.Datetime()
    winner_production_last_updated = fields.Datetime()
    external_sales_order_no = fields.Char(string="Clockwork")

    sales_project_id = fields.Many2one('sales.projects', string='Project')
    apartment_id = fields.Many2one('sales.projects.apartment', string="Apartment")

    supplier_confirmed = fields.Boolean(string='Bekreftelse mottatt', default=False, copy=False)

    order_type = fields.Selection(selection=[
        ('exhibit', 'Exhibition'),
        ('standard', 'Standard'),
        ('builder', 'Builder'),
        ('campaign', 'Campaign'),
        ('project', 'Project'),
    ], string="Order Type")

    warranty_identification = fields.Char()
    warranty_selected = fields.Boolean(string='Warranty')
    builder_partner_id = fields.Many2one('res.partner', domain="[('is_builder', '=', True)]")
    this_day = fields.Date(default=fields.Datetime.now)
    price_campaign_id = fields.Many2one('strai.campaign', string="Campaign", domain="['&', ('from_date', '<=', this_day), ('to_date', '>=', this_day)]")
    tag_ids = fields.Many2many('crm.tag')

    is_production = fields.Boolean(related="company_id.production")

    booked_by_store = fields.Boolean()

    eno = fields.Boolean(default=False, string="ENO")

    store_name = fields.Char("Butikk navn")
    store_user_name = fields.Char("Selger navn (butikk)")
    store_user_email = fields.Char("Selger e-post (butikk)")

    remarks = fields.Char()

    builder_agreement_situation = fields.Selection([
        ('builder_direct', 'Builder buys directly'),
        ('referral', 'Referral'),
        ('optional_customer', 'Optional customer')
    ])

    mail_sent_counter = fields.Integer(default=0)
    po_sent = fields.Boolean(string="Innkjøp sendt", default=False)

    # transport date from ordreboka, the date when the final order (entire sale order) is sent from HUB
    logistic_send_date = fields.Date()
    # sale order is produced on the Evert production line at this date
    productionline_date = fields.Date()

    # categorize countertops and other purchases, the order office should do countertop purchase and purchase dep. the other ones
    is_countertop_order = fields.Boolean(store=True, readonly=False, compute='compute_is_countertop_order')

    store_warranty_order = fields.Boolean(string="Selgerfeil")
    # order_ack_received = fields.Boolean(string="Ordrebekreftelse mottatt")
    order_ack_checked = fields.Boolean(string="Bekreftelse sjekket")

    purchase_order_name_store = fields.Char(string="Innkjøp butikk", compute="_compute_purchase_order_name_store", store=True)

    @api.onchange('apartment_id')
    def get_analytic_account(self):
        if self.apartment_id:
            for line in self.order_line:
                line.analytic_distribution = {str(self.apartment_id.analytic_account_id.id): 100} 
        else:
            for line in self.order_line:
                line.analytic_distribution = False

    @api.onchange('order_type')
    def onchange_order_type_clear_fields(self):
        # reset fields on changing order_type
        for record in self:
            if record.order_type != 'project':
                record.sales_project_id = False
                record.apartment_id = False
            if record.order_type != 'campaign':
                record.price_campaign_id = False
            if record.order_type != 'builder':
                record.builder_partner_id = False
                record.builder_agreement_situation = False

    def write(self, vals):
        # if not self.user_id and 'user_id' not in vals and self.env.user.id != ResUser.Trunk.value:  # do not set Trunk user as purchaser
        #     vals['user_id'] = self.env.user.id
        # elif 'user_id' in vals and vals['user_id'] == False and self.env.user.id != ResUser.Trunk.value:  # do not set Trunk user as purchaser
        #     vals['user_id'] = self.env.user.id
        if 'user_id' in vals and vals['user_id'] == ResUser.Trunk.value:
            vals['user_id'] = False
        return super(PurchaseOrder, self).write(vals)

    def _prepare_line_values(self, line_data, order, products):
        return {
            'product_id': products[line_data['product']['reference']],
            'product_uom_qty': line_data.get('quantity'),
            'order_id': order.id,
            'position': line_data.get('item_position'),
            'name': line_data['product']['name'],
            'price_unit': line_data['product']['sale_price']
        }

    def _prepare_write_values(self, line_data):
        return {
            'price_unit': line_data['product']['sale_price'],
        }

    def get_picking_type(self):
        picking_id = self.env['stock.picking.type'].search([('sequence_code', '=', 'IN')]).id
        return picking_id

    # def winner_ref_order(self, order_data, production_company):
    #     if order_data.get('sale_reference'):
    #         winner_reference_order = self.env['sale.order'].sudo().search(
    #             [('origin', '=', order_data['sale_reference']), ('company_id', '=', production_company.id)])
    #         return winner_reference_order

    def get_tag_ids(self, order_data):
        trunk_tags = [t_tag.capitalize() for t_tag in order_data['tags']]
        odoo_tags = self.env['crm.tag'].search([('name', 'in', trunk_tags)])

        tags_to_create = list(set(trunk_tags) - set(odoo_tags.mapped('name')))
        tag_ids = [self.env['crm.tag'].sudo().create({'name': t}).id for t in
                   tags_to_create] if tags_to_create else []
        tag_ids.extend(odoo_tags.ids)

        return tag_ids

    def remove_as_follower(self, order, email):
        for follower in order.message_follower_ids:
            if follower.partner_id.email == email:
                follower.sudo().unlink()

    # Pulls data from SO to PO
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # pulls data from so to po
            if vals.get('origin'):
                sale_order = self.env['sale.order'].search([('name', '=', vals['origin'])])
                if sale_order:
                    # if sale_order.order_type == 'exhibit' and not sale_order.sale_to_self and not sale_order.is_production:
                    #     return False
                    vals.update({
                        'delivery_phone_one': sale_order.delivery_phone_one,
                        'delivery_phone_two': sale_order.delivery_phone_two,
                        'delivery_floor_id': sale_order.delivery_floor_id.id,
                        'info_transport': sale_order.info_transport,
                        'info_production': sale_order.info_production,
                        'info_accounting': sale_order.info_accounting,
                        'delivery_type_id': sale_order.delivery_type_id.id,
                        'product_type_id': sale_order.product_type_id.id,
                        'order_attachment_ids': sale_order.order_attachment_ids,
                        'winner_reference': sale_order.winner_reference,
                        'winner_reference_production': sale_order.winner_reference_production,
                        'date_planned': sale_order.commitment_date,
                        'production_date': sale_order.production_date,
                        'sale_reference': sale_order.origin,
                        'capacity_booking_deadline': sale_order.capacity_booking_deadline,
                        'order_type': sale_order.order_type,
                        'builder_partner_id': sale_order.builder_partner_id.id,
                        'price_campaign_id': sale_order.price_campaign_id.id,
                        'store_responsible_id': sale_order.user_id.id,
                        'delivery_method_id': sale_order.delivery_method_id.id,
                        'visma_project': sale_order.visma_project,
                        'origin_sales_order_no': sale_order.name,
                        'winner_file_id': sale_order.winner_file_id,
                        'winner_last_updated': sale_order.winner_last_updated,
                        'winner_production_last_updated': sale_order.winner_production_last_updated,
                        'sales_project_id': sale_order.sales_project_id.id,
                        'apartment_id': sale_order.apartment_id.id,
                        'booked_by_store': sale_order.booked_by_store,
                        'warranty_selected': sale_order.warranty_selected,
                        'external_sales_order_no': sale_order.external_sales_order_no,  # let Strai Krs add external sales order no with ENO orders
                        'eno': sale_order.eno,
                        'store_name': sale_order.company_id.name if not sale_order.is_production else sale_order.store_name,
                        'store_user_name': sale_order.user_id.name if not sale_order.is_production else sale_order.store_user_name,
                        'store_user_email': sale_order.user_id.partner_id.email if not sale_order.is_production else sale_order.store_user_email,
                        'remarks': sale_order.remarks,
                        'builder_agreement_situation': sale_order.builder_agreement_situation,
                        'store_warranty_order': sale_order.store_warranty_order
                    })
                    if sale_order.order_type == 'exhibit' and not sale_order.is_production and sale_order.sale_to_self:
                        vals.update({
                            'exhibit_analytic_account_id': sale_order.exhibit_analytic_account_id.id,
                        })

                        if sale_order.analytic_account_id != sale_order.exhibit_analytic_account_id:
                            sale_order.analytic_account_id.unlink()
                        if sale_order.opportunity_id:
                            sale_order.opportunity_id.unlink()
                        if sale_order.activity_ids:
                            sale_order.activity_ids.unlink()

                        sale_order.analytic_account_id = sale_order.exhibit_analytic_account_id

                        # disable warning dialog to be able to automatically cancel sale order
                        sale_order.action_cancel()
                        sale_order.message_post(body="Utstilling er OK, men tilbudet er kansellert fordi tilbudet ikke skal faktureres kunde.")
            # get correct delivery location. See also _onchange_warehouse
            if vals.get('partner_id'):
                partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
                if self.env.company.id and partner_id and partner_id.picking_type_id:
                    vals['picking_type_id'] = partner_id.picking_type_id.id
        return super(PurchaseOrder, self).create(vals_list)

    # Pulls data from PO to intercompany SO
    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        res = super(PurchaseOrder, self)._prepare_sale_order_data(name, partner, company, direct_delivery_address)

        # Multicompany access right problem if we do not allow multicompany on attachments
        for attachment in self.order_attachment_ids:
            attachment.allow_multicompany = True

        company_prod = self.env['res.company'].sudo().search([('production', '=', True)], limit=1)
        res.update(
            {
                'info_transport': self.info_transport,
                'info_production': self.info_production,
                'info_accounting': self.info_accounting,
                'delivery_floor_id': self.delivery_floor_id.id,
                'delivery_phone_one': self.delivery_phone_one,
                'delivery_phone_two': self.delivery_phone_two,
                'delivery_type_id': self.delivery_type_id.id,
                'product_type_id': self.product_type_id.id,
                'order_attachment_ids': self.order_attachment_ids,
                'winner_reference': "{}/{}".format(self.company_id.id, self.winner_reference),
                'winner_reference_production': self.winner_reference_production,
                'commitment_date': self.env['sale.order'].search([('name', '=', self.origin_sales_order_no)]).commitment_date or self.date_planned,
                'production_date': self.production_date,
                'origin': self.sale_reference,
                'capacity_booking_deadline': self.capacity_booking_deadline,
                'store_responsible_id': self.store_responsible_id.id,
                'delivery_method_id': self.delivery_method_id.id,
                'sales_project_id': self.sales_project_id.id,
                'apartment_id': self.apartment_id.id,
                'visma_project': self.visma_project,
                'origin_sales_order_no': self.origin_sales_order_no,
                'winner_file_id': self.winner_file_id,
                'winner_last_updated': self.winner_last_updated,
                'winner_production_last_updated': self.winner_production_last_updated,
                'order_type': self.order_type,
                'builder_partner_id': self.builder_partner_id.id,
                'price_campaign_id': self.price_campaign_id.id,
                'warranty_identification': self.warranty_identification,
                'warranty_selected': self.warranty_selected,
                'tag_ids': [(6, 0, [t.id for t in self.tag_ids])],
                'booked_by_store': self.booked_by_store,
                'external_sales_order_no': self.external_sales_order_no,  # handle ENO orders from Strai Krs
                'eno': self.eno,
                'store_name': self.store_name,
                'store_user_name': self.store_user_name,
                'store_user_email': self.store_user_email,
                'opportunity_id': self.env['crm.lead'].sudo().search([('partner_id', '=', partner.id), ('company_id', '=', company_prod.id), ('intercompany_lead', '=', True)]).id,
                'remarks': self.remarks,
                'builder_agreement_situation': self.builder_agreement_situation,
                'store_warranty_order': self.store_warranty_order
            }
        )
        return res

    # Transfers fields to resulting Invoices
    def _prepare_invoice(self):
        vals = super(PurchaseOrder, self)._prepare_invoice()
        vals.update({
            'product_type_id': self.product_type_id,
            'order_type': self.order_type,
            'remarks': self.remarks,
            'sales_project_id': self.sales_project_id.id,
            'apartment_id': self.apartment_id.id,
            'builder_partner_id': self.builder_partner_id.id,
            'builder_agreement_situation': self.builder_agreement_situation,
            'price_campaign_id': self.price_campaign_id.id,
            'store_warranty_order': self.store_warranty_order,
            'store_name': self.store_name
        })
        return vals

    # handle automatic address when changing to/from drop-ship in PO
    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):
        for po in self:
            if po.picking_type_id.name == "Dropship" and po.origin:
                origin_so = self.env['sale.order'].search([('name', 'ilike', po.origin)])
                if origin_so:
                    po.dest_address_id = origin_so.partner_shipping_id.id
            else:
                po.dest_address_id = False

    @api.onchange('partner_id')
    def _onchange_warehouse(self):
        if self.is_production and self.partner_id.picking_type_id:
            self.picking_type_id = self.partner_id.picking_type_id.id

    def button_confirm(self):
        company_prod = self.env['res.company'].sudo().search([('production', '=', True)], limit=1)
        """Adds line postions numbers if their is none"""
        for po in self:
            # validate that it is not a duplicate - cancel / draft / re-confirm case. Should be cancelled in factory before confirmed again
            if not po.is_production and po.partner_id.id == company_prod.partner_id.id:
                winner_ref_shop = f'{po.company_id.id}/{po.winner_reference}'
                factory_order = self.env['sale.order'].sudo().search([('winner_reference', '=', winner_ref_shop), ('state', '!=', 'cancel'), ('company_id', '=', company_prod.id)])
                if factory_order:
                    raise UserError(_('Du har allerede sendt bestilling på Winner %s. Vennligst be ordrekontoret kansellere %s før du bestiller på nytt.',po.winner_reference, factory_order.client_order_ref))
                # set to False, so that Odoo standard sets it to the correct value
                # if it is already set (confirmed before), and then cancelled and confirmed again, only the old value will be here
                po.partner_ref = False

            pos_number = 0
            for line in po.order_line:
                if line.position == 0 or not line.position:
                    line.position = pos_number
                    pos_number += 1

            if not po.user_id and self.env.user.id != ResUser.Trunk.value:
                po.user_id = self.env.user.id

            # add to Trunk queue, so Trunk will be notified that there is a new confirmed purchase order
            # Trunk uses this information to integrate to Ordreboka and mark orders as purchased
            # only care about purchase orders in production company
            if po.company_id.production:
                self.env['trunk.queue'].create_queue_item(TaskType.confirmed_purchase_order_production, self._name, po.id, po.name)

            # Set po_sent to True when a store confirms a PO to the factory
            if po.partner_id == company_prod.partner_id:
                po.po_sent = True

            # Remove outgoing quantities in regular deliveries in related SO if there are any
            if po.default_location_dest_id_usage == 'customer':
                for po_line in po.order_line:
                    relevant_moves = po_line.sale_line_id.move_ids.filtered(lambda l: l.state not in ('done', 'cancel') and l.picking_id.picking_type_id.sequence_code == 'OUT')
                    for rel_move in relevant_moves:
                        rel_move.state = 'draft'
                        rel_move.unlink()

        return super(PurchaseOrder, self).button_confirm()

    def button_cancel(self):
        company_prod = self.env['res.company'].sudo().search([('production', '=', True)], limit=1)
        for po in self:
            # First check if the SF in the production company exists, failsafe with checking on only winner_ref
            if not po.is_production and po.partner_id.id == company_prod.partner_id.id and po.state in ['purchase', 'done']:
                winner_ref_shop = f'{po.company_id.id}/{po.winner_reference}'
                factory_order = self.env['sale.order'].sudo().search([('winner_reference', '=', winner_ref_shop), ('state', '!=', 'cancel'), ('company_id', '=', company_prod.id)])
                if factory_order:
                    if factory_order.state == 'draft' and not factory_order.user_id:
                        po.message_post(body=_('%s er ikke behandlet på ordrekontoret enda. Innkjøpet er derfor også kansellert i fabrikk.', po.name))
                        factory_order.message_post(body=_('Selger har kansellert %s, og %s er kansellert automatisk.', po.name, factory_order.name))
                        self.env.user.notify_info(message=_('%s er ikke behandlet på ordrekontoret enda. Innkjøpet er derfor også kansellert i fabrikk. Når kansellering i fabrikk er bekreftet, kan %s kanselleres.', po.name, po.name))
                        self._cancel_intercompany_saleorder(factory_order.id)
                    elif factory_order.user_id and factory_order.state not in ['sale', 'done', 'cancel']:
                        raise UserError(_('%s er under behandling på ordrekontoret. Vennligst send mail til ordre@strai.no for kansellering i fabrikk.') % po.name)
                    elif factory_order.state in ['sale', 'done']:
                        raise UserError(_('%s er ferdig behandlet på ordrekontoret, og eventuelle innkjøp hos underleverandør er gjort. Vennligst send mail til ordre@strai.no for å høre om kansellering er mulig i fabrikk. Når kansellering i fabrikk er bekreftet, kan %s kanselleres.', po.name, po.name))
        return super(PurchaseOrder, self).button_cancel()

    # workaround with Trunk call, and Trunk calls back to Odoo with action_cancel on specified sale order
    # not possible to cancel directly without access, even with sudo
    # in the future, make a module that Odoo can use to call itself from outside without using Trunk
    def _cancel_intercompany_saleorder(self, sale_order_id):
        # capture staging branches in SH, do not run this function in staging because it will always trigger in production
        if self.env['ir.config_parameter'].sudo().get_param('database.is_neutralized'):
            return

        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        operation_mode_id = ir_config_parameter.get_param('strai.trunk_mode')
        operation_mode = self.env['trunk.endpoint'].search([('id', '=', operation_mode_id)])
        endpoint = '/Order/CancelSaleorder'
        payload = {
            'saleOrderId': sale_order_id,
        }

        headers = {
            'ApiKey': ir_config_parameter.get_param('strai.trunk_password'),
            'ApiClient': ir_config_parameter.get_param('strai.trunk_username')
        }

        response = requests.request("POST", operation_mode.endpoint + endpoint, headers=headers, data=payload)
        if not response.ok:
            raise UserError(_('Det oppstod et problem med kansellering. Prøv igjen eller kontakt ordrekontoret.'))

    def action_rfq_send(self):
        self.mail_sent_counter += 1
        if self.state in ['purchase', 'done']:
            self.po_sent = True
        return super().action_rfq_send()

    @api.depends('order_line')
    def compute_is_countertop_order(self):
        for po in self:
            for line in po.order_line:
                if line.product_id.categ_id.parent_path and line.product_id.categ_id.parent_path.startswith('1/8/'):
                    po.is_countertop_order = True
                    break
                else:
                    po.is_countertop_order = False

    # Method for All and My purchase where production=False
    @api.model
    def retrieve_dashboard(self):
        result = super(PurchaseOrder, self).retrieve_dashboard()
        # easy counts
        po = self.env['purchase.order']
        result['all_to_send'] = po.search_count([('state', 'not in', ['purchase', 'done', 'cancel'])])
        result['my_to_send'] = po.search_count([('state', 'not in', ['purchase', 'done', 'cancel']), ('user_id', '=', self.env.uid)])
        result['all_waiting'] = po.search_count([('state', 'in', ['purchase', 'done']),('supplier_confirmed', '=', False),('order_ack_checked', '=', False)])
        result['my_waiting'] = po.search_count([('state', 'in', ['purchase', 'done']),('supplier_confirmed', '=', False),('order_ack_checked', '=', False),('user_id', '=', self.env.uid)])
        result['all_late'] = po.search_count([('state', 'in', ['purchase', 'done']), ('supplier_confirmed', '=', True),('order_ack_checked', '=', False),('is_production', '=', False)])
        result['my_late'] = po.search_count([('state', 'in', ['purchase', 'done']),('supplier_confirmed', '=', True),('order_ack_checked', '=', False),('user_id', '=', self.env.uid)])

        return result 

    def copy(self, default=None):
        retval = super(PurchaseOrder, self).copy(default)
        if self.origin:
            retval.origin = self.origin
        return retval

    @api.ondelete(at_uninstall=False)
    def _unlink_trunk_queue_check(self):
        for order in self:
            trunk_queue_rec = self.env['trunk.queue'].sudo().search([('res_name', '=', order.name)], limit=1)
            if trunk_queue_rec:
                raise UserError(_('A record in the trunk queue already exists. Therefore, the PO cannot be deleted, but should be left cancelled in the system.'))
    # def action_confirmation_ok(self):
    #     self.order_ack_confirmed = True

    @api.depends('origin')
    def _compute_purchase_order_name_store(self):
        for po in self:
            if po.is_production and po.origin:
                po.purchase_order_name_store = self.env['sale.order'].sudo().search([('name', '=', po.origin)], limit=1).client_order_ref
            else:
                po.purchase_order_name_store = po.name