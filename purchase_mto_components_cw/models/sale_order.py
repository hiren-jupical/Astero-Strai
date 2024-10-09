import json

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..enums.product_route_enum import ProductRouteEnum
from ..enums.picking_type_enum import PickingTypeEnum
from ..enums.stock_location_enum import StockLocationEnum


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_mto_created = fields.Boolean(string='Purchase MTO created', default=False)
    purchase_mto_stock_updated = fields.Boolean(default=False)

    def _action_confirm(self):
        for order in self:
            if order.is_production and not order.purchase_mto_created:
                order.purchase_mto_components_cw()
        return super(SaleOrder, self)._action_confirm()

    def purchase_mto_components_cw(self):
        for order in self:
            # data validation
            if not order.external_sales_order_no:
                raise UserError(_(f'Clockwork SO must be set correctly to get the components from Clockwork: {order.name}'))
            if not order.is_production:
                raise UserError(_(f'MTO components from Clockwork can only generate purchase orders in production company: {order.name}'))

            order.purchase_mto_created = True

            # missing_products = []
            # get components
            components = order.get_components_from_trunk()
            for component in components:
                # connect to product
                product = self._get_product_by_default_code_partner_ref_product_code(component['Itmcod'], component['SupplierRef'], component['SupplierProductCode'])
                if not product:
                    # what to do if product does not exist? raise error for now
                    raise UserError(_(f'Product could not be found: {component["Itmcod"]} {component["Itmnam"]}. Contact purchase department.'))
                    # missing_products.append({'itmcod': component["Itmcod"], 'itmnam': component["Itmnam"]})

                # only create / update purchase orders on products that are purchase to order
                if len(product.route_ids.filtered(lambda x: x.id == ProductRouteEnum.BuyMto.value or x.id == ProductRouteEnum.RefillOnOrder.value)) > 0:
                    # will only append to purchase orders that are in draft state
                    purchase_order = order.get_purchase_order(component['SupplierRef'])
                    order.create_purchase_order_line(purchase_order, product, component['Quantity'])

    def _get_product_by_default_code_partner_ref_product_code(self, default_code, partner_id_ref, product_code):
        product = self.env['product.product'].search([('default_code', '=', default_code)])
        # if product not found based on reference, try to get it using supplier + supplier product code
        if not product:
            supplier = self.env['res.partner'].search([('ref', '=', partner_id_ref)])
            if supplier:
                product_supplierinfo = self.env['product.supplierinfo'].search([('partner_id', '=', supplier.id), ('product_code', '=', product_code)])
                if product_supplierinfo and product_supplierinfo.product_id:
                    product = product_supplierinfo.product_id
        return product

    @api.model
    def get_purchase_order(self, partner_ref):
        # get / create purchase order
        partner_id = self.env['res.partner'].search([('ref', '=', partner_ref)])
        if not partner_id:
            raise UserError(_('Supplier does not exist'))
        purchase_order = self.env['purchase.order'].search([('origin', '=', self.name), ('partner_id', '=', partner_id.id), ('state', '=', 'draft')])
        if not purchase_order:
            purchase_order = self.env['purchase.order'].create({
                'partner_id': partner_id.id,
                'picking_type_id': self.env['stock.picking.type'].search([('sequence_code', '=', 'IN'), ('warehouse_id', '=', 'Strai Kjøkken AS'), ('barcode', '=', 'STRAI-RECEIPTS')], limit=1).id,
                'date_planned': self.commitment_date,
                'external_sales_order_no': self.external_sales_order_no,
                'origin': self.name,
                'mto_purchase': True,
                'user_id': False,
                'currency_id': partner_id.property_purchase_currency_id.id
            })
        return purchase_order

    @api.model
    def create_purchase_order_line(self, purchase_order, product, qty):
        # append lines to purchase order
        self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': product.id,
            'product_qty': qty
        })

    def _cron_update_mto_stock(self, limit):
        # get sale orders where MTO purchase orders might have been made, and stock has not been updated, but sale order is sent
        sale_orders = self.env['sale.order'].search([('purchase_mto_created', '=', True), ('purchase_mto_stock_updated', '=', False), ('invoice_status', 'in', ['to invoice', 'invoiced'])], limit=limit)
        sale_orders.mto_update_stock()

    def mto_update_stock(self):
        for order in self:
            purchase_orders = self.env['purchase.order'].search([('origin', '=', order.name), ('mto_purchase', '=', True), ('mto_stock_updated', '=', False)])
            for po in purchase_orders:
                stock_picking = self.env['stock.picking'].create({
                    'picking_type_id': PickingTypeEnum.StockFromClockwork.value,
                    'partner_id': po.partner_id.id,
                    'location_id': StockLocationEnum.StraiLager.value,
                    'location_dest_id': StockLocationEnum.PartnerLocationsCustomers.value,
                    'origin': f'Clockwork/{order.name}/{po.name}/{po.external_sales_order_no}',
                    'scheduled_date': order.commitment_date,
                })
                for order_line in po.order_line:
                    self.env['stock.move'].create({
                        'picking_id': stock_picking.id,
                        'location_id': StockLocationEnum.StraiLager.value,
                        'location_dest_id': StockLocationEnum.PartnerLocationsCustomers.value,
                        'product_id': order_line.product_id.id,
                        'product_uom_qty': order_line.product_uom_qty,
                        'name': order_line.name,
                        'procure_method': 'make_to_stock',  # actually make_to_order, but we don't want it to generate another purchase order automatically
                    })
                # re-update this field, as it resets itself when adding lines to it
                stock_picking.scheduled_date = order.commitment_date

                # confirm stock picking
                stock_picking.action_confirm()
                stock_picking.action_assign()
                stock_picking.button_validate()

                po.mto_stock_updated = True
            order.purchase_mto_stock_updated = True

    @api.model
    def get_components_from_trunk(self):
        response = requests.request("GET", self._get_base_endpoint() + f'/Rainbow/GetCwBom?sonr={self.external_sales_order_no}', headers=self._get_default_headers())
        if response and response.ok:
            components = json.loads(response.content)
            return components
        else:
            if response.text:
                bom_error = json.loads(response.text)
                if bom_error.get('detail'):
                    raise UserError(_('ERROR: BOM failure in Clockwork. Error:\n%s\n\nContact Martin for correction', bom_error.get('detail')))
            raise UserError(_('ERROR: not able to get components from Trunk'))

    def _get_base_endpoint(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        operation_mode_id = ir_config_parameter.get_param('strai.trunk_mode')
        trunk_endpoint = self.env['trunk.endpoint'].search([('id', '=', operation_mode_id)])
        return trunk_endpoint.endpoint

    def _get_default_headers(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        headers = {
            'ApiKey': ir_config_parameter.get_param('strai.trunk_password'),
            'ApiClient': ir_config_parameter.get_param('strai.trunk_username'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return headers
