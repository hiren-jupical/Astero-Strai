from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    producttype_ordertype_mandatory = fields.Boolean(default=False, string="Mandatory product type and order type")
