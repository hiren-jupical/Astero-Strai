from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    activate_vendor_pr_line = fields.Boolean(related='company_id.activate_vendor_pr_line')
