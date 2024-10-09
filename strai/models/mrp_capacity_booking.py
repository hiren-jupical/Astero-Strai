from odoo import fields, models, _
import logging

_logger = logging.getLogger(__name__)
ENDPOINT = '/Rainbow/GetProductionCapacity'

CAPACITY = [
    ('no_capacity', 'No Capacity'),
    ('low', 'Low Capacity'),
    ('good', 'Good Capacity')]


class CapacityBooking(models.Model):
    _name = 'mrp.capacity.booking'
    _description = 'Capacity'
    _order = 'delivery_week, delivery_year, id'

    delivery_week = fields.Integer()
    delivery_year = fields.Integer()
    capacity = fields.Selection(CAPACITY)

    # cronjob for synching this table with data from trunk
    def _cron_update_table(self):
        content = self.env['strai.trunk'].get_data_from_trunk(ENDPOINT)
        # If the year and week is allready in the recordset: write. Else: create
        for date in content:
            record = self.env['mrp.capacity.booking'].search([('delivery_week', '=', date['Week']), ('delivery_year', '=', date['Year'])], limit=1)
            if record.id:
                # We have an update
                record.write({
                    'delivery_week': date['Week'],
                    'delivery_year': date['Year'],
                    'capacity': CAPACITY[date['Capacity']][0]
                })
            else:
                # create a new entry
                record.create({
                    'delivery_week': date['Week'],
                    'delivery_year': date['Year'],
                    'capacity': CAPACITY[date['Capacity']][0]
                })
