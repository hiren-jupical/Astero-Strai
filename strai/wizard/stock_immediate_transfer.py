from odoo import fields, models, _
import logging

# Part of Odoo. See LICENSE file for full copyright and licensing details.

_logger = logging.getLogger(__name__)


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        """ Adds functionality to the standard odoo method 'process' from the stock.immediate.transfer wizard
            Automatically confirms the multicompany purchase order-delivery that has created the sale order
            Furthemore, it also changes qty_delivered on the purchase order line to the delivered amount"""
        place = False
        # Do not do anything if the delivery confirmed is not for a customer (internal stock transfers)
        for pick in self.pick_ids:
            if pick.location_dest_id.usage == "customer":
                place = 'customer'
        if place == 'customer':
            own_sale_order = False
            partner_purchase_order = False
            done_descriptions = []
            # List of descriptions not used for anything here
            for delivery in self.pick_ids:
                for line in delivery.move_line_ids:
                    done_descriptions.append(line.move_id.description_picking)
                if delivery.sale_id:
                    # own_sale_order = self.env['sale.order'].search([('name', '=', delivery.origin)])
                    own_sale_order = delivery.sale_id
                    if own_sale_order:
                        self._deliver_service(own_sale_order)
                if delivery.products_availability_state != 'available' or delivery.backorder_id.id:
                    return super(StockImmediateTransfer, self).process()
            partner_company = self.env['res.company'].sudo().search([('name', '=', own_sale_order.partner_id.name)])
            if partner_company:
                partner_purchase_order = self.env['purchase.order'].sudo().search([('name', '=', own_sale_order.client_order_ref), ('company_id', '=', partner_company.id)])
            if partner_purchase_order != False:
                origin_order = self.env['sale.order'].sudo().search([('name', '=', partner_purchase_order.origin)])
                if origin_order:
                    self._deliver_service(origin_order)
                    self._deliver_service_po(partner_purchase_order)
                partner_stock_move = self.env['stock.picking'].sudo().search([('origin', '=', partner_purchase_order.name)], limit=1)
                for move_line in partner_stock_move.move_line_ids:
                    move_line.qty_done = move_line.reserved_uom_qty
                if partner_stock_move:
                    partner_stock_move.with_company(partner_company.id).button_validate()

        return super(StockImmediateTransfer, self).process()

    def _deliver_service(self, order):
        for line in order.order_line:
            if line.product_type == 'service':
                line.qty_delivered = line.product_uom_qty

    def _deliver_service_po(self, order):
        for line in order.order_line:
            if line.product_type == 'service':
                line.qty_received = line.product_qty
