from odoo import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('cust_invoice_id'):
                vals.update({'extract_state': 'done'})
        return super().create(vals_list)
