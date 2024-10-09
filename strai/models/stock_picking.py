from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    buyer_id = fields.Many2one('res.partner')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('origin'):
                sale_order = self.env['sale.order'].search([('name', '=', vals['origin'])])

                if sale_order:
                    vals.update({
                        'buyer_id': sale_order.partner_id.id})
        return super(StockPicking, self).create(vals_list)
