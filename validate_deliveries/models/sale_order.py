# -- coding: utf-8 --
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
import logging

from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = "sale.order"

    def _cron_validate_deliveries(self, limit):
        sale_orders = self.sudo().search([
            ('delivery_confirmed', '=', True),
            ('delivery_completed', '=', False),
            ('picking_ids', '!=', False)], limit=limit)
        # sale_orders = self.sudo().search([('name', '=', 'SF23184061')])
        exhibition_orders = self.sudo().search([
            ('order_type', '=', 'exhibit'),
            ('sale_to_self', '=', False),
            ('state', 'in', ['sale', 'done']),
            ('delivery_completed', '=', False),
            ('is_production', '=', False),
            ('picking_ids', '!=', False)])
        sale_orders = [j for i in [sale_orders, exhibition_orders] for j in i]
        for order in sale_orders:
            _logger.info('****Delivery marked as fulfilled***: {}'.format(order.name))
            # If any uncomfirmed purchase orders for the sale order, confirm them and validate deliveries
            # if order.purchase_order_count > 0:
            #     self.confirm_po(order)
            # If any deliveries for the sale order, validate them

            place = False
            stock_pickings = self.env['stock.picking'].search([
                ('sale_id', '=', order.id),
                ('state', 'not in', ['cancel', 'done'])]).sorted(key=lambda s: s.picking_type_code)
            context = {}
            for stock_picking in stock_pickings:
                if stock_picking.location_dest_id.usage == "customer":
                    place = 'customer'
                for move in stock_picking.move_ids.filtered(lambda l: l.state not in ('done', 'cancel')):
                    move.quantity = move.product_uom_qty
                    total_quantity = sum(move.move_line_ids.mapped('quantity'))

                    if total_quantity != move.quantity:
                        if move.move_line_ids:
                            total = 0.0
                            for index, move_line in enumerate(move.move_line_ids):
                                remaining_quantity = move.product_uom_qty - total

                                # If this is the last move_line, assign the remaining quantity
                                if index == len(move.move_line_ids) - 1:
                                    move_line.quantity = remaining_quantity
                                else:
                                    if total >= move.product_uom_qty:
                                        move_line.quantity = 0
                                    else:
                                        move_line.quantity = min(move_line.quantity, remaining_quantity)

                                total += move_line.quantity

                        else:
                            self.env['stock.move.line'].create({
                                'company_id': stock_picking.company_id.id,
                                'date': stock_picking.scheduled_date,
                                'product_id': move.product_id.id,
                                'picking_type_id': stock_picking.picking_type_id.id,
                                'picking_id': stock_picking.id,
                                'move_id': move.id,
                                'quantity': move.product_uom_qty
                                })
                try:
                    if stock_picking.state in ('confirmed', 'waiting'):
                        context.update({
                            'skip_sanity_check': True,
                        })
                    stock_picking.with_context(**context).button_validate()
                except UserError as ue:
                    _logger.error("Feil med stock.picking {} / sale.order {}. Feilmelding\n{}".format(stock_picking.name, order.name, ue))
            if place and place == 'customer':
                partner_purchase_order = partner_company = False
                # List of descriptions not used for anything here
                for delivery in stock_picking.move_line_ids:
                    if delivery.picking_id.products_availability_state != 'available' or delivery.picking_id.backorder_id.id:
                        continue

                partner_company = self.env['res.company'].sudo().search([('name', '=', order.partner_id.name)], limit=1)
                order._deliver_service()
                if partner_company:
                    partner_purchase_order = self.env['purchase.order'].sudo().search([('name', '=', order.client_order_ref), ('company_id', '=', partner_company.id)], limit=1)
                if partner_purchase_order != False:
                    origin_order = self.env['sale.order'].sudo().search([('name', '=', partner_purchase_order.origin)], limit=1)
                    if origin_order:
                        origin_order._deliver_service()
                        self._deliver_service_po(partner_purchase_order)

                        # get stock moves of receipt created from purchase order with intercompany
                        partner_stock_moves = self.env['stock.picking'].sudo().search([
                            ('purchase_id', '=', partner_purchase_order.id),
                            ('state', 'not in', ['cancel', 'done'])]).sorted(key=lambda s: s.picking_type_code)

                        # partner_stock_moves = self.env['stock.picking'].sudo().search([
                        #     ('sale_id', '=', origin_order.id),
                        #     ('state', 'not in', ['cancel', 'done'])]).sorted(key=lambda s: s.picking_type_code)

                        for stock_picking in partner_stock_moves:
                            for move in stock_picking.move_ids:
                                total = 0.0
                                for move_line in move.move_line_ids:
                                    move_line.quantity = move.product_uom_qty
                                    total += move.product_uom_qty
                                    if total >= move.product_uom_qty:
                                        break
                            if stock_picking:
                                try:
                                    stock_picking.with_company(partner_company.id).button_validate()
                                except UserError as ue:
                                    _logger.error(
                                        "Feil med stock.picking {} / sale.order {}. Feilmelding\n{}".format(
                                            stock_picking.name, order.name, ue))
            order.delivery_completed = True

    def confirm_po(self, order):
        purchase_orders = self.env['purchase.order'].search([('state', 'not in', ['cancel', 'purchase'])])
        for po in purchase_orders:
            _logger.info(po)
            s_orders = po._get_sale_orders().ids
            if order.id in s_orders:
                po.button_confirm()
                stock_move = self.env['stock.picking'].search([('origin', '=', po.name), ('state', 'not in', ['cancel', 'done'])])
                for move in stock_move.move_ids:
                    total = 0.0
                    for move_line in move.move_line_ids:
                        move_line.quantity = move.product_uom_qty
                        total += move.product_uom_qty
                        if total >= move.product_uom_qty:
                            break
                stock_move.button_validate()
                order._deliver_service_po(po)

    def _deliver_service(self):
        for line in self.order_line:
            if line.product_type == 'service':
                line.qty_delivered = line.product_uom_qty

    def _deliver_service_po(self, order):
        for line in order.order_line:
            if line.product_type == 'service':
                line.qty_received = line.product_qty
