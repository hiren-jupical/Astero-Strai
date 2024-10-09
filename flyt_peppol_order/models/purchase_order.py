# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
from odoo import models, fields, api, _
from odoo.addons.account_edi_ubl_cii.models.account_edi_common import UOM_TO_UNECE_CODE, EAS_MAPPING
from odoo.tools import float_repr, float_round


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    peppol_edi = fields.Selection([
            ('unprocessed', 'Un Processed'),
            ('processed', 'Processed'),
        ], string="PEPPOL Status", help="Purchase Order File Status", readonly=True)
    edi_send_purchase_order_confirmation = fields.Boolean(related='partner_id.edi_send_purchase_order_confirmation')
    order_response_code = fields.Selection(
        string="PEPPOL Response Status",
        copy=False,
        selection=[('AB', 'Order received'),
                ('RE', 'Order Rejected'),
                ('AP', 'Order Accepted w/o changes'),
                ('CA', 'Order Accepted w/ changes'),
            ],
        readonly=True)
    edi_order_confirmation_validated = fields.Boolean("Order Confirmation Validated", copy=False)

    @api.depends('order_line.date_planned')
    def _compute_date_planned(self):
        if self.env.context.get('skip_date_planned_recompute'): # Skip recomputing date_planned
            return
        return super()._compute_date_planned()

    def button_confirm(self):
        purchase_order = super().button_confirm()
        self.filtered("partner_id.edi_send_purchase_order_confirmation").write({'peppol_edi': 'unprocessed'})
        return purchase_order

    def button_cancel(self):
        purchase_order = super().button_cancel()
        self.filtered("partner_id.edi_send_purchase_order_confirmation").write({'peppol_edi': ''})
        return purchase_order

    def button_draft(self):
        purchase_order = super().button_draft()
        self.filtered("partner_id.edi_send_purchase_order_confirmation").write({'peppol_edi': ''})
        return purchase_order

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _get_uom_unece_code(self, line):
        xmlid = line.product_uom.get_external_id()
        if xmlid and line.product_uom.id in xmlid:
            return UOM_TO_UNECE_CODE.get(xmlid[line.product_uom.id], 'C62')
        return 'C62'

    def format_float(self, amount, precision_digits):
        if amount is None:
            return None
        return float_repr(float_round(amount, precision_digits), precision_digits)

    def _get_peppol_scheme_id(self, partner):
        country_code = partner._deduce_country_code()
        scheme_id = EAS_MAPPING.get(country_code, False) and next(iter(EAS_MAPPING[country_code].keys()))
        return scheme_id or ''

    # -------------------------------------------------------------------------
    # Purchase Order Response EDI Process Function
    # -------------------------------------------------------------------------

    # @api.model
    def update_order_from_peppol_response(self, all_orders_data, status=False):
        error_docs, valid_docs = [], []
        self._peppol_update_context()
        for order_data in all_orders_data:
            data = self.update_from_peppol_data(
                order_data['order_reference_id'],
                order_data['buyer_customer_party_endpoint_id'],
                order_data['order_data'],
                order_data['order_lines_data'],
                status
            )
            doc = {order_data['order_reference_id']: order_data['doc_id']}
            if not data:
                error_docs.append(doc)
            else:
                valid_docs.append(doc)
        return {'error_docs' : error_docs, 'valid_docs': valid_docs}

    def update_from_peppol_data(self, order_reference_id, buyer_customer_party_endpoint_id, order_data, order_lines_data, status=False):
        purchase_order = self.search([('name', '=ilike', order_reference_id)])
        # Uncomment the next line if needed to match the endpoint ID
        # purchase_order = self.search([('name', '=', order_reference_id), ('company_id.l10n_no_bronnoysund_number', '=', buyer_customer_party_endpoint_id)])

        if not purchase_order:
            return

        order_values = {
            'order_response_code': order_data.get('OrderResponseCode', ''),
            'edi_order_confirmation_validated': False,
        }

        purchase_order.update(order_values)
        product_model = self.env['product.product']
        line_updates, new_lines = [], []

        for line_data in order_lines_data:
            line_id = line_data.get('line_id')
            standard_item_id = line_data.get('standard_item_id')
            product = product_model.search([('seller_ids.product_code', '=', standard_item_id)], limit=1)

            po_line = purchase_order.order_line.filtered(
                lambda line: (line_id.isdigit() and line.peppol_line_id == int(line_id)) or standard_item_id in line.product_id.seller_ids.mapped('product_code')
            )
            if len(po_line) > 1:
                po_line = po_line.filtered(lambda l: line_id.isdigit() and l.peppol_line_id == int(line_id))
            if po_line:
                confirmed_price = float(line_data.get('confirmed_price', 0.0) or 0.0)
                confirmed_qty = float(line_data.get('confirmed_qty', 0.0) or 0.0)
                price_qty_mismatch = False
                if confirmed_price and confirmed_price != po_line.price_unit:
                    purchase_order.message_post(body=_( '%s - The confirmed price does not match the price in Odoo') % (po_line.product_id.display_name))
                    price_qty_mismatch = True
                if confirmed_qty and confirmed_qty != po_line.product_qty:
                    purchase_order.message_post(body=_( '%s - The confirmed quantity does not match the ordered quantity') % (po_line.product_id.display_name))
                    price_qty_mismatch = True

                line_updates.append({
                    'po_line': po_line,
                    'values': {
                        'confirmed_qty': confirmed_qty,
                        'confirmed_price': confirmed_price,
                        'line_status_code': line_data.get('LineStatusCode', ''),
                        'date_planned': line_data.get('expected_arrival', ''),
                        'note': line_data.get('note', ''),
                        'price_qty_mismatch': price_qty_mismatch,
                    }
                })
            elif (not po_line and line_data.get('LineStatusCode') == '1') or status:
                if product:
                    new_lines.append({
                        'peppol_line_id': max(purchase_order.order_line.mapped('peppol_line_id')) + 1,
                        'order_id': purchase_order.id,
                        'product_id': product.id,
                        'confirmed_qty': float(line_data.get('confirmed_qty', 0.0)),
                        'confirmed_price': float(line_data.get('confirmed_price', 0.0)),
                        'date_planned': line_data.get('expected_arrival', ''),
                        'note': line_data.get('note', ''),
                        'line_status_code': '1'
                    })
                else:
                    purchase_order.message_post(body=f"Product {line_data.get('ProductName', '')} was not found. Product Code {standard_item_id} does not exist.")
            else:
                purchase_order.message_post(body=f"Orderline {standard_item_id} did not match any supplier vendor code in Odoo. Please check this line manually.")

        for update in line_updates:
            update['po_line'].update(update['values'])

        if new_lines:
            self.env['purchase.order.line'].create(new_lines)

        purchase_order.message_post(body=_("Electronic order confirmation received from %s") % (purchase_order.partner_id.name))
        return True

    def _peppol_update_context(self):
        context = dict(self.env.context)
        context.update({
            'skip_date_planned_recompute': True,
        })
        self.env.context = context

    # -------------------------------------------------------------------------
    # Purchase EDI Process Field Function
    # -------------------------------------------------------------------------

    @api.model
    def get_peppol_purchase_orders_json(self):
        po_list = []
        peppol_purchase_ids = self.search([('peppol_edi', '=', 'unprocessed')])
        for po in peppol_purchase_ids:
            po_list.append(po._export_purchase_order_vals())
            po.peppol_edi = 'processed'
        return po_list

    def _export_purchase_order_vals(self):
        order_lines = self.order_line.filtered(lambda line: line.product_qty and line.display_type not in ('line_note', 'line_section'))
        vals =  {
            'order' : {**self._prepare_purchase_order_vals(), **{'OrderLine': [self._prepare_purchase_order_line_vals(line) for line in order_lines]}}
        }
        return {'purchase_id': str(self.id), 'purchase_vals': json.dumps(vals, indent=4, sort_keys=False, default=str)}

    def _prepare_purchase_order_vals(self):
        return {
            'ID': self.name,
            'IssueDate': self.create_date.date(),
            'IssueTime': self.create_date.time().replace(microsecond=0),
            'Note': self.notes.striptags() if self.notes else '',
            'DocumentCurrencyCode': self.currency_id.name,
            'CustomerReference': self.company_id.peppol_customer_ref,
            'OrderDocumentReference_ID': self.name,
            'BuyerCustomerParty': self._prepare_BuyerCustomerParty_vals(),
            'SellerSupplierParty': self._prepare_SellerSupplierParty_vals(),
            'Delivery': self._prepare_Delivery_vals(),
        }

    def _prepare_purchase_order_line_vals(self, line):
        product_supplierinfo_id = line.product_id._select_seller(partner_id=line.order_id.partner_id, quantity=line.product_qty)
        currency_dp = line.currency_id.decimal_places
        return {
            'id' : line.peppol_line_id,
            'Quantity': line.product_qty,
            'unitCode': self._get_uom_unece_code(line) ,
            'LineExtensionAmount': self.format_float(line.product_qty * line.price_unit, currency_dp),
            'LineExtensionAmount_currencyID': line.currency_id.name,
            'Price_PriceAmount': self.format_float(line.price_unit, currency_dp),
            'Price_PriceAmount_currencyID': line.currency_id.name,
            'Item_Description': line.name,
            'Item_Name': line.product_id.name,
            'Item_BuyersItemIdentification_ID': line.product_id.default_code,
            'Item_SellersItemIdentification_ID': product_supplierinfo_id and product_supplierinfo_id.product_code or ''
        }

    def _prepare_PostalAddress_vals(self, partner):
        return {
            'StreetName': partner.street,
            'CityName': partner.city,
            'PostalZone': partner.zip,
            'Country_IdentificationCode': partner.country_id.code,
        }

    def _prepare_BuyerCustomerParty_vals(self):
        return {
            'EndpointID': self.company_id.l10n_no_bronnoysund_number,
            'EndpointID_schemeID': self._get_peppol_scheme_id(self.company_id.partner_id),
            'PartyIdentification_ID': self.company_id.l10n_no_bronnoysund_number,
            'PartyIdentification__schemeID': self._get_peppol_scheme_id(self.company_id.partner_id),
            'PartyName_Name': self.company_id.name,
            'PostalAddress': self._prepare_PostalAddress_vals(self.company_id),
            'PartyLegalEntity_RegistrationName': self.company_id.name,
            'PartyLegalEntity_CompanyID': self.company_id.l10n_no_bronnoysund_number,
            'PartyLegalEntity_CompanyID_schemeID': self._get_peppol_scheme_id(self.company_id.partner_id),
            'PartyLegalEntity_RegistrationAddress_CityName': self.company_id.city,
            'PartyLegalEntity_RegistrationAddress_Country_IdentificationCode': self.company_id.country_id.code,
            'Contact_Name': self.user_id.name,
            'Contact_Telephone': self.user_id.phone,
            'Contact_ElectronicMail': self.user_id.login,
        }

    def _prepare_SellerSupplierParty_vals(self):
        return {
            'EndpointID': self.partner_id.l10n_no_bronnoysund_number,
            'EndpointID_schemeID': self._get_peppol_scheme_id(self.company_id.partner_id),
            'PartyIdentification_ID': self.partner_id.l10n_no_bronnoysund_number,
            'PartyIdentification_ID_schemeID': self._get_peppol_scheme_id(self.company_id.partner_id),
            'PartyName_Name': self.partner_id.name,
            'PostalAddress': self._prepare_PostalAddress_vals(self.partner_id),
            'PartyLegalEntity_RegistrationName': self.partner_id.name,
        }

    def _prepare_Delivery_vals(self):
        is_dropship = self.dropship_picking_count
        partner_id = is_dropship and self.dest_address_id or self.picking_type_id.warehouse_id.partner_id
        return {
            'DeliveryLocation_ID': is_dropship and 'drop_shipment' or self.company_id.l10n_no_bronnoysund_number,
            'Address': self._prepare_PostalAddress_vals(partner_id),
            'RequestedDeliveryPeriod_EndDate': self.date_planned.date(),
            'DeliveryParty_PartyIdentification_ID': self.partner_ref,
            'DeliveryParty_PartyName_Name': self.dest_address_id.parent_id.name or self.dest_address_id.name if \
                is_dropship else self.picking_type_id.display_name,
            'DeliveryParty_Contact_Name': partner_id.name,
            'DeliveryParty_Contact_Telephone': partner_id.phone,
            'DeliveryParty_Contact_ElectronicMail': partner_id.email
        }
