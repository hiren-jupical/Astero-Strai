from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_edi = fields.Boolean()
    purchase_edi_endpoint = fields.Char()
    purchase_edi_colors = fields.One2many('purchase.edi.color', 'partner_id', string='Available colors')
