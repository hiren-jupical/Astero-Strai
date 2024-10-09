from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_line_name = fields.Text(related='sale_line_id.name')
