from odoo import api, fields, models, _


class ResCompanySettings(models.Model):
    _inherit = 'res.company'
    _name = 'res.company'

    # vendor bills configuration fields
    enable_vendor_triple_approval = fields.Boolean(string="Enable Vendor Bill Approval")
    director_approval_amount_vendor = fields.Monetary(string="Director Approval Amount", default=0.0)
    manager_approval_user_id_vendor = fields.Many2one('res.users', string='Manager Approval User')
    director_approval_user_id_vendor = fields.Many2one('res.users', string='Director Approval User')
    apply_auto_complete_overruling = fields.Boolean(string="Enable Auto Complete overruling")

    po_responsible_person = fields.Boolean(string='Check PO Responsible Person')
