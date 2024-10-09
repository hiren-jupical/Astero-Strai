from odoo import api, fields, models, _


class DeliveryFloor(models.Model):
    _name = 'delivery.floor'
    _description = 'Delivery Floor'
    _order = 'sequence, id'

    name = fields.Char('Delivery Floor')
    delivery_floor = fields.Selection([('floor', 'Floor')], string='Type', default='floor', required=True)
    sequence = fields.Integer(help="Determine the display order", default=10)
