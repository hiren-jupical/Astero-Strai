from odoo import api, fields, models, _


class DeliveryType(models.Model):
    _name = 'delivery.type'
    _description = 'Delivery Type'
    _order = 'sequence, id'

    name = fields.Char('Delivery Type')
    delivery_type = fields.Selection([('transport', 'Transport')], string='Type', default='transport', required=True)
    sequence = fields.Integer(help="Determine the display order", default=10)
