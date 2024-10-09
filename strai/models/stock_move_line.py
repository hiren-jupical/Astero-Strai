from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    position = fields.Integer(string="no.", related='move_id.sale_line_id.position')
    position_in = fields.Integer(related='move_id.purchase_line_id.position')

    original_sale_order_line = fields.Char()
