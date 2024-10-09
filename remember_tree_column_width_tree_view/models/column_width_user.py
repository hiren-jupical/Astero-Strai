
from odoo import api, fields, models


class ColumnFieldWidthUser(models.Model):
    _name = "column.field.width.user"

    view_id = fields.Many2one('ir.ui.view', ondelete='cascade', required=True)
    field_name = fields.Text('Field Name', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    width = fields.Integer(string="Width", required=True)

    _sql_constraints = [
        ('user_id_view_id_field_name', 'unique(view_id, field_name, user_id)',
         'View Name, Field Name User Id must be unique.'),
    ]


class ResUsers(models.Model):
    _inherit = "res.users"

    column_field_width_lines = fields.One2many(
        comodel_name='column.field.width.user',
        inverse_name='user_id',
        string="Column Field Width Lines",
        copy=True, auto_join=True)



