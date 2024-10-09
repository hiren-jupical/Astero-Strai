from odoo import models, fields, api


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    store_name = fields.Char(string="Butikknavn", readonly=True)

    def _select(self):
        return super(PurchaseReport, self)._select() + ", po.store_name"

    # def _from(self):
    #     return super()._from() + " "
