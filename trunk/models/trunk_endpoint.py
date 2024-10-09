from odoo import models, fields, api, _


class TrunkEndpoint(models.Model):
    _name = 'trunk.endpoint'
    _description = 'Trunk endpoint'

    name = fields.Char()
    endpoint = fields.Char()
