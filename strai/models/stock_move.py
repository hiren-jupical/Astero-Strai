from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    position = fields.Integer(string="pos", related='sale_line_id.position')
    position_in = fields.Integer(string="Position IN", related='purchase_line_id.position')

    # override standard function from stock/models/stock_move to include assigned and waiting stages
    # this function desides if you need to click on button and enter receival/sent goods in the dialog,
    # or if you could just enter received/sent goods directly in list view.
    # you can enter directly in list view when this function returns false

    # This feature is deprecated in v17.
    # def _show_details_in_draft(self):
    #     show = super()._show_details_in_draft()
    #     # if standard says it should show, test if it is in assigned / waiting stage, and then set to false if that is the case
    #     if show:
    #         if self.state in ['draft', 'waiting', 'assigned']:
    #             show = False
    #     return show
