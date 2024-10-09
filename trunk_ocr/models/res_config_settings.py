from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_trunk = fields.Boolean(string="Trunk Integration", related='company_id.enable_trunk', readonly=False)
