from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    trunk_operation_mode = fields.Selection(selection=[
        ('production', 'Production'),
        ('test', 'Test'),
        ('development', 'Development/Debugging')
    ], config_parameter='strai.trunk_operation_mode')
    trunk_mode = fields.Many2one("trunk.endpoint", config_parameter='strai.trunk_mode')
    trunk_username = fields.Char(config_parameter='strai.trunk_username')
    trunk_password = fields.Char(config_parameter='strai.trunk_password')
