from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _cron_validate_stock_picking(self, limit):
        company_prod = self.env['res.company'].search([('production', '=', True)], limit=1)
        stock_pickings = self.env['stock.picking'].search([('company_id', '=', company_prod.id), ('picking_type_id', '=', 219), ('scheduled_date', '<=', fields.Date.today()), ('state', 'in', ('draft', 'waiting', 'confirmed', 'assigned'))], limit=limit)
        context = {
            'skip_sanity_check': True
        }
        for picking in stock_pickings:
            for move in picking.move_ids:
                if move.move_line_ids:
                    for line in move.move_line_ids:
                        line.qty_done = move.product_uom_qty
                else:
                    # create line manually
                    self.env['stock.move.line'].create({
                        'company_id': company_prod.id,
                        'date': picking.scheduled_date,
                        'product_id': move.product_id.id,
                        'picking_type_id': picking.picking_type_id.id,
                        'picking_id': picking.id,
                        'move_id': move.id,
                        'qty_done': move.product_uom_qty
                    })
            picking.move_ids._set_quantities_to_reservation()
            picking.with_context(**context).button_validate()
