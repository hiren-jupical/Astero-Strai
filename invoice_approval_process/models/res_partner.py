from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    purchase_responsible_person_id = fields.Many2one('res.users', 'Purchase Responsible Person', help="Select a Purchase Resposible Person", company_dependent=True)
    force_director_approval = fields.Many2one('res.users', string='Force Director Approval',
                                              help='If this field filled, Partner assigned Invoices or Vendor Bills will need director approval from this user', company_dependent=True)
