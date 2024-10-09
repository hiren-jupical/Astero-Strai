from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    auto_approval_enabled = fields.Boolean('Auto approval enabled', help='Set up this supplier to be able to automatically approve invoices based on purchase orders')
    auto_approval_max_residual_total = fields.Float('Max residual total', help='Maximum allowed total residual amount for an invoice to be automatically approved')
    auto_approval_max_amount = fields.Float('Max amount', help='Total amount that goes above this sum, will need manual approval')
    auto_approval_validate_kid = fields.Boolean('Validate KID', help='Validate that a KID is set on invoices before approving')
    auto_approval_require_received_products = fields.Boolean('Require received products', help='All products in purchase order should be received before invoice could be approved')
    auto_approval_validate_account = fields.Boolean('Validate financial account', help='All lines should have the same account as specified on the supplier. If no account is specified on supplier, this will invalidate both approval and posting')
    auto_approval_auto_post = fields.Boolean('Auto post', help='Auto post invoice/creditnote if all conditions are satisfied')
