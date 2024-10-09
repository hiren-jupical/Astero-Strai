from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    company_id = fields.Many2one('res.company', 'Company', default=False, ondelete='cascade', readonly=False)

    _sql_constraints = [
        ('unique_number', 'unique(sanitized_acc_number, company_id, partner_id)', 'Account Number must be unique'),
    ]
