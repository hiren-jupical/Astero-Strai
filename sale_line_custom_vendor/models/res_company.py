from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    activate_vendor_pr_line = fields.Boolean(company_dependent=True)
