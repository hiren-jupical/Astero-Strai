from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    attach_e01_purchase = fields.Boolean('Attach E01 file', help='Attach E01 file to purchase orders from this supplier', required=False, default=False)
