from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    # override std field, add compute method and store=True to auto-calculate on order changes
    product_uom_qty = fields.Float(
        'Demand',
        digits='Product Unit of Measure',
        default=1.0, required=True,
        help="This is the quantity of products from an inventory "
             "point of view. For moves in the state 'done', this is the "
             "quantity of products that were actually moved. For other "
             "moves, this is the quantity of product that is planned to "
             "be moved. Lowering this quantity does not generate a "
             "backorder. Changing this quantity on assigned moves affects "
             "the product reservation, and should be done with care.",
        store=True, compute='compute_product_uom_qty')

    def _prepare_procurement_values(self):
        res = super(StockMove, self)._prepare_procurement_values()
        res.update({
            'sale_line_id': self.sale_line_id.id, 
            'so_line_id': self.sale_line_id.id,
            'sale_order': self.sale_line_id.order_id,
            'current_vendor': self.sale_line_id.current_vendor
        })
        return res

    # the total qty on purchase order should equal the total quantity of stock.move's
    @api.depends('purchase_line_id.product_qty', 'sale_line_id.product_uom_qty')
    def compute_product_uom_qty(self):
        for move in self:
            if move._change_should_be_handled() and move.picking_code == 'incoming':
                other_moves = move.picking_id.move_ids.filtered(lambda x: x.purchase_line_id and x.purchase_line_id == move.purchase_line_id and x.id != move.id)
                other_move_qty = 0.0
                for other_move in other_moves:
                    other_move_qty += other_move.product_uom_qty

                update_quantity_done = move.quantity > 0.0 and move.state in ('draft', 'waiting', 'assigned', 'confirmed')
                move.product_uom_qty = move.purchase_line_id.product_qty - other_move_qty
                if update_quantity_done:
                    move.quantity = move.product_uom_qty
                if move.purchase_line_id.order_id.partner_id.order_changes_should_be_synchronized: #Remember for v17: only execute the fct below in cases of synchronization (i.e. only one PO)
                    move.update_out_move(move.picking_code)
                if move.product_uom_qty <= 0.0:
                    for other_move in other_moves.filtered(lambda x: x.product_uom_qty > 0.0):
                        qty_reduction = min(move.product_uom_qty * -1, other_move.product_uom_qty)
                        if qty_reduction > 0.0:
                            other_move.product_uom_qty -= qty_reduction
                            move.product_uom_qty += qty_reduction  # negative qty, adding the reduction to reduce the negative
                            if update_quantity_done:
                                move.quantity = move.product_uom_qty
                            move.update_out_move(move.picking_code)
                        else:
                            # no more to reduce, either reduced successfully or there is still a negative qty on the move
                            # could include more pickings from same supplier in editable states, but it adds a lot of complexity
                            # leave it as is for now
                            break
            if move.picking_code == 'outgoing':
                move.update_out_move(move.picking_code)

    @api.model
    def update_out_move(self, picking_code):
        if self.sale_line_id:
            out_move = self.env['stock.move'].search([('picking_code', '=', 'outgoing'), ('sale_line_id', '=', self.sale_line_id.id), ('state', 'in', ['draft', 'waiting', 'assigned', 'confirmed'])], limit=1)
            if out_move:
                update_quantity_done = out_move.state in ('draft', 'waiting', 'assigned', 'confirmed') and out_move.quantity > 0.0
                out_move.product_uom_qty = self.product_uom_qty if picking_code == 'incoming' else self.sale_line_id.product_qty
                if update_quantity_done:
                    out_move.quantity = out_move.product_uom_qty


    @api.model
    def _change_should_be_handled(self):
        # confirmed is actually "waiting"
        return self.state in ['draft', 'waiting', 'confirmed', 'assigned'] and self.picking_id
