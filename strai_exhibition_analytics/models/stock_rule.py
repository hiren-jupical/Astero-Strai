from odoo import api, models
import logging
_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_buy(self, procurements):
        origin = procurements[0][0].origin
        sale_order = self.env['sale.order'].search([('name', '=', origin)])
        if sale_order and sale_order.order_type == 'exhibit' and not sale_order.is_production and not sale_order.sale_to_self:
            return False
        return super(StockRule, self)._run_buy(procurements)
