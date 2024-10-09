from odoo import fields, models, api, _
import random

class MaintenanceRequestTag(models.Model):
    _name = "maintenance.request.tag"
    _description = "Maintenance Request Tag"
    _sql_constraints = [
        ("check_unique_name", "UNIQUE(name)", "The name must be unique"),
    ]
    name = fields.Char('Tag Name', required=True)
    color = fields.Integer('Color Index')

    def create(self, vals):
        vals['color'] = random.randint(1, 11)

        result = super(MaintenanceRequestTag, self).create(vals)
        return result

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    tag_ids = fields.Many2many('maintenance.request.tag', string="Tagger")
