from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    priority = fields.Boolean()

    is_mto = fields.Boolean('Split PO lines')

    is_builder = fields.Boolean()
    is_production = fields.Boolean(compute='compute_is_production')
    internal_pricelist_id = fields.Many2one('product.pricelist', company_dependent=True, domain="[('order_type', '=', 'builder')]")

    picking_type_id = fields.Many2one('stock.picking.type', string='Standard Warehouse', )

    independent_shop = fields.Boolean(default=False)

    external_customer_identifier = fields.Char("Eksternt kundenr")

    no_price_compare_cw = fields.Boolean(default=False, string="Ikke sammenlign pris mot CW")

    winnerref = fields.Char("Winner referanse")
    winner_customers = fields.One2many('winner.customer', 'partner_id', string='Winner kunder')

    residual_product = fields.Many2one('product.product', string='Residual produkt', help='Price residual between purchase orders and invoice. Choose which product the residual should be accounted on')
    standard_account = fields.Many2one('account.account', string='Standard account', company_dependent=True, required=False, default=False)
    standard_product = fields.Many2one('product.product', string='Standard product', required=False, default=False)

    industry = fields.Selection([
        ('arkitekt', 'Arkitekt'),
        ('byggfirma_bygger_hus', 'Byggfirma (bygger hus)'),
        ('byggfirma_bygger_ikke_hus', 'Byggfirma (bygger ikke hus)'),
        ('byggmesterforeningen', 'Byggmesterforeningen'),
        ('eiendomsmegler', 'Eiendomsmegler'),
        ('eiendomsutvikler', 'Eiendomsutvikler'),
        ('entreprenør', 'Entreprenør'),
        ('interiorarkitekt', 'Interiørarkitekt'),
        ('interiorkonsulent', 'Interiørkonsulent'),
        ('kommune', 'Kommune'),
        ('montor', 'Montør'),
        ('rorlegger', 'Rørlegger'),
        ('skade_forsikringselskap', 'forsikringselskap'),
        ('takstmann', 'Takstmann'),
        ('annet', 'Annet')
    ], required=False, default=False, string="Bransje")
    agreement_type = fields.Char(string="Avtaletype", compute="_compute_agreement_type", readonly=True, store=False)  # show selected pricelist in factory
    agreement_info = fields.Text(string="Info om avtalen")
    main_builder = fields.Many2one('res.partner', string="Hovedavtale", domain="[('is_builder', '=', True)]")
    invoice_option = fields.Selection([
        ('strai', 'Strai'),
        ('proffkunde', 'Proffkunde'),
    ], required=False, string="Hvem fakturerer tilvalg?", default="strai")
    invoice_referral = fields.Selection([
        ('strai', 'Strai'),
        ('proffkunde', 'Proffkunde'),
    ], required=False, string="Hvem fakturerer henvisning?", default="strai")
    agreement_start_date = fields.Date(string="Avtalen gjelder fra")
    builder_discount_matrix = fields.One2many('res.partner.builder.discount.matrix', 'partner_id', 'Rabattmatrise', compute='compute_builder_discount_matrix', readonly=False, store=True)
    builder_agreement_file = fields.Binary(string='Avtale')
    builder_agreement_filename = fields.Char(string='Avtale filnavn')

    default_leadtime = fields.Integer(string="Default leadtime", required=False, default=14, help='Set leadtime on new products to this value')

    active = fields.Boolean(tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for partner in res:
            if partner.type in ['delivery', 'invoice'] and partner.priority:
                same_type_addr = partner.parent_id.child_ids.filtered(lambda p: p.type == partner.type and p != partner and p.priority)
                if same_type_addr:
                    same_type_addr.priority = False
        return res

    def write(self, vals):
        list_users = self.env['res.users'].search([])
        for partner in self:
            phone = vals.get('phone')
            if partner.id in [user.partner_id.id for user in list_users]:
                partner.check_user_phone(phone)
        res = super().write(vals)
        for partner in self:
            if vals.get('priority'):
                if partner.type in ['delivery', 'invoice'] and partner.priority:
                    same_type_addr = partner.parent_id.child_ids.filtered(lambda p: p.type == partner.type and p != partner and p.priority)
                    if same_type_addr:
                        same_type_addr.priority = False
        return res

    # Always create a delivery address for the customer
    # There needs to be traceability in case the customer changes address
    # When a new delivery address is changed, or a mistake on the delivery address is corrected - 
    # the address on the parent partner also needs to be changed
    # If there is no address on the parent partner, the delivery address is automatically -
    # added as the parent partners address (Standard Odoo)
    def create_contact(self, contact_data, contact_type):
        # handle direct imports from factory, map to correct customer both own shops and independent shops
        if contact_type == 'contact' and contact_data['reference'].startswith('1/'):
            existing_contact = self.env['winner.customer'].search([('customer_number', '=', contact_data['reference'][2:])], limit=1).partner_id
            if existing_contact:
                return existing_contact.id

        # if not from factory and known contact, run normal procedure
        existing_contact = self.env['res.partner'].search([('ref', '=', contact_data['reference']), ('name', '=', contact_data['name'])], limit=1)
        values = self._prepare_values(contact_data)
        values.update({
            'type': contact_type,
            'phone': contact_data.get('phone', False) or False,
            'mobile': contact_data.get('mobile', False) or False
        })

        # address_match = False
        existing_address = False
        if existing_contact and contact_type != 'contact':
            # existing_address = existing_contact.child_ids.filtered(lambda r: r.type == contact_type and r._validate_address(contact_data))
            existing_addresses = self.env['res.partner'].search([('parent_id.id', '=', existing_contact.id), ('active', 'in', [True, False]), ('type', '=', contact_type), ('winnerref', '=', contact_data['winner_reference'])])
            existing_address = existing_addresses.filtered(lambda r: r._validate_address(contact_data))
            if len(existing_address) > 1:
                existing_address = existing_address[0]
            # address_match = existing_address.filtered(lambda r: r._validate_address(contact_data))

        # If the customer exists and there is an address matching the order data, return existing customer
        if existing_address:
            return existing_address.id

        # If the customer exists, but the address from the NEW (update is false) order does not match any known address - Create new delivery/invoice address:
        if existing_contact:
            current_contact = existing_contact
            if contact_type != 'contact':
                values.update({
                    'parent_id': existing_contact.id,
                    'ref': False,
                    'name': False,
                    'mobile': False,
                    'phone': False,
                    'winnerref': contact_data['winner_reference']
                })
                # if existing_address:
                #     current_contact = self.env['res.partner'].search([('id', '=', existing_address.id)])
            if contact_type == 'delivery':
                values.update({'priority': True})
                # always create new delivery address if changed to avoid changing historic deliveries
                current_contact = self.env['res.partner'].create(values)
            elif contact_type == 'invoice':
                values.update({'priority': True})
                # always create new invoice address if changed to avoid changing historic deliveries
                current_contact = self.env['res.partner'].create(values)

            # update customer if main contact
            current_contact.write({**values})
            return current_contact.id

        if not existing_contact:
            base_partner = self.env['res.partner'].create(values)
            return base_partner.id

    def address_get(self, adr_pref=None):
        result = super().address_get(adr_pref)
        if 'delivery' in result:
            # delivery_addr = self.child_ids.filtered(lambda c: c.type == 'delivery' and c.priority)
            delivery_addr = self.env['res.partner'].search([('parent_id.id', '=', result['contact']), ('active', 'in', [True, False]), ('type', '=', 'delivery')])
            if len(delivery_addr) > 1:
                delivery_addr = delivery_addr[0]
            result['delivery'] = delivery_addr.id if delivery_addr else result['delivery']
        if 'invoice' in result:
            invoice_addr = self.env['res.partner'].search([('parent_id.id', '=', result['contact']), ('active', 'in', [True, False]), ('type', '=', 'invoice')])
            if len(invoice_addr) > 1:
                invoice_addr = invoice_addr[0]
            result['invoice'] = invoice_addr.id if invoice_addr else result['invoice']
        return result

    def _set_delivery_priority(self):
        if self.parent_id and self.type in ['delivery', 'invoice']:
            addresses = self.parent_id.child_ids.filtered(lambda r: r.type == self.type and r.priority and r != self)
            if addresses:
                addresses.priority = False
            self.priority = True

    def _validate_address(self, data):
        if not self.street == data['street']:
            return False
        if not self.city == data['city']:
            return False
        if not self.zip == data['zip']:
            return False
        if not self.street2 == data.get('street2'):
            return False
        return True

    def _prepare_values(self, contact_data):
        values = {
            'name': contact_data['name'],
            'ref': contact_data['reference'],
            'email': contact_data['email'],
            'phone': contact_data['phone'],
            'street': contact_data['street'],
            'city': contact_data['city'],
            'zip': contact_data['zip'],
            'company_type': 'company' if contact_data.get('is_company') else 'person',
            'mobile': contact_data.get('mobile'),
            'street2': contact_data.get('street2'),
            'vat': contact_data.get('vat'),
            'website': contact_data.get('website'),
            # [166, "Norge"]
            'country_id': 166,
            'country_code': 'NO',
            'lang': 'nb_NO'
        }
        return values

    def check_user_phone(self, phone):
        if phone:
            users = self.env['res.users'].search([])
            for user in users:
                if user.phone == phone:
                    raise UserError(_(f"Two users cannot have the samme phone number. User: {user.name} already has number: {phone}"))

    # For hidding internal pricelist in the stores
    def compute_is_production(self):
        for record in self:
            record.is_production = record.env.company.production

    @api.depends('property_product_pricelist')
    def _compute_agreement_type(self):
        company_production = self.env['res.company'].search([('production', '=', True)], limit=1)
        for partner in self:
            partner_id = partner.id if partner.id else partner.id.origin  # I get "NewId" in some cases, even though it already exists. Using origin solve this
            partner.write({
                'agreement_type': self.env['res.partner'].sudo().with_company(company_production.id).search([('id', '=', partner_id)]).property_product_pricelist.name
            })

    @api.depends('property_product_pricelist')
    def compute_builder_discount_matrix(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        special_pricelist_id = ir_config_parameter.get_param('strai.builder_special_pricelist')
        for record in self:
            # problems with "NewId"
            if not record.id:
                continue
            # only re-calculate if changes are done in production. Pricelist in other companies are irrelevant for this
            if self.env.company.production:
                # get discount matrix from price list, if it is not the special pricelist
                # do not update anything if the special pricelist is selected
                # update if special_pricelist_id if not set
                # update if pricelist selected is different from special_pricelist_id
                if not special_pricelist_id or not record.property_product_pricelist.id == int(special_pricelist_id):
                    pricelist_discount_matrix = self.env['product.pricelist.builder.discount.matrix'].search([('product_pricelist_id', '=', record.property_product_pricelist.id)])
                    # delete all records in res.partner, and copy each line from pricelist into res partner
                    # a lot of problems with "NewId" records, it deletes other info fields as well
                    record.builder_discount_matrix.unlink()
                    # for discount in record.builder_discount_matrix:
                    #     self.env['res.partner.builder.discount.matrix'].browse(discount.id).unlink()
                    # copy pricelist discount matrix to res partner discount matrix
                    for discount in pricelist_discount_matrix:
                        self.env['res.partner.builder.discount.matrix'].create({
                            'partner_id': record.id,
                            'product_category_id': discount.product_category_id.id,
                            'product_brand_id': discount.product_brand_id.id,
                            'product_series_id': discount.product_series_id.id,
                            'agreement_discount': discount.agreement_discount,
                            'customer_discount_option': discount.customer_discount_option,
                            'customer_discount_referral': discount.customer_discount_referral,
                            'commission_option': discount.commission_option,
                            'commission_referral': discount.commission_referral
                        })

    @api.onchange('builder_discount_matrix')
    def onchange_builder_discount_matrix(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        special_pricelist_id = ir_config_parameter.get_param('strai.builder_special_pricelist')
        for record in self:
            if not special_pricelist_id:
                raise UserError('Proff spesial prisliste er ikke satt')
            if not record.property_product_pricelist == int(special_pricelist_id):
                # check if contents of pricelist discount matrix equals partner discount matrix
                # if not, set special pricelist
                partner_matrix = sorted([(d.product_category_id.id, d.product_brand_id.id, d.product_series_id.id, d.agreement_discount, d.customer_discount_option, d.customer_discount_referral, d.commission_option, d.commission_referral) for d in record.builder_discount_matrix])
                pricelist_matrix = sorted([(d.product_category_id.id, d.product_brand_id.id, d.product_series_id.id, d.agreement_discount, d.customer_discount_option, d.customer_discount_referral, d.commission_option, d.commission_referral) for d in self.env['product.pricelist.builder.discount.matrix'].search([('product_pricelist_id', '=', record.property_product_pricelist.id)])])
                if partner_matrix != pricelist_matrix:
                    record.property_product_pricelist = int(special_pricelist_id)
