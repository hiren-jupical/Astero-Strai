from odoo import fields, models, api, _
from datetime import datetime

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    @api.model
    def year_selection(self):
        year = 1970
        year_list = []
        while year <= 2099:  # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    manufacturer_partner_id = fields.Many2one(comodel_name='res.partner', string="Produsent")

    production_year = fields.Selection(
        year_selection,
        string="Produksjonsår"
    )

    nominal_power_usage = fields.Char(string="Nominelt strømtrekk")

    air_consumption = fields.Char(string="Luftforbruk")

    suction = fields.Char(string="Avsug")

    weight = fields.Char(string="Egenvekt")

    total_dimension = fields.Char(string="Total dimensjon")

    service_and_parts_partner_id = fields.Many2one(comodel_name="res.partner", string="Kontaktinfo service og delebestilling")

