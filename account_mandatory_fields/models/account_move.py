from odoo import models, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        self.check_mandatory_fields()
        return super().action_post()

    def action_first_approval(self):
        self.check_mandatory_fields()
        return super().action_first_approval()

    def action_second_approval(self):
        self.check_mandatory_fields()
        return super().action_second_approval()

    def check_mandatory_fields(self):
        for move in self:
            valid = move.check_validity()
            if not valid:
                move.raise_validation_error()

    @api.model
    def check_validity(self):
        valid = True
        if self.line_ids and (not self.product_type_id or not self.order_type):
            # journal items, not invoice items. Should also block misc journals
            for line in self.line_ids:
                if line.account_id and line.account_id.producttype_ordertype_mandatory:
                    valid = False
                    break
        return valid

    def raise_validation_error(self):
        raise ValidationError(_('Mandatory field not set. Check product type and order type'))
