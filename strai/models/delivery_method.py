from odoo import api, fields, models, _


class DeliveryMethod(models.Model):
    _name = 'delivery.method'
    _description = 'Delivery Method'
    _order = 'sequence, id'

    name = fields.Char('Delivery Method')
    delivery_method = fields.Selection([('terms', 'Terms')], string="Type", default='terms', ondelete="cascade")
    sequence = fields.Integer(help="Determine the display order", default=10)
