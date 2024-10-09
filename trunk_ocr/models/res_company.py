from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_trunk = fields.Boolean(string="Trunk Integration")
