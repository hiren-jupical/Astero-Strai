from odoo import models, fields


class PurchaseEdiColor(models.Model):
    _name = 'purchase.edi.color'
    _rec_name = 'color'  # standard displayed name in relationships

    partner_id = fields.Many2one('res.partner')
    color = fields.Char(required=True)
    itemcode = fields.Char(required=True)
    # TODO maybe handle special?
