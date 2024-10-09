from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    order_changes_should_be_synchronized = fields.Boolean(default=False)
