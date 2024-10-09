from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    activate_vendor_pr_line = fields.Boolean(related='company_id.activate_vendor_pr_line')
