from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    mto_purchase = fields.Boolean(default=False, string="MTO purchase")
    mto_stock_updated = fields.Boolean(default=False, string="MTO Stock updated")
