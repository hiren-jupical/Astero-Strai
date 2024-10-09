from odoo import models, fields, _


class StockRoute(models.Model):
    _inherit = 'stock.route'

    product_company_ids = fields.Many2many(
        'res.company', 'stock_route_company', 'route_id', 'company_id',
        'Companies', copy=False)
    code = fields.Char()
