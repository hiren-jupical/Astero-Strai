
from odoo import api, models, _
from odoo.exceptions import ValidationError

from . import kid_validation

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        for record in self:
            if record.move_type != 'in_invoice':
                continue
            if record.payment_reference:                
                valid = all([x.isdigit() or x=='-' for x in record.payment_reference]) and kid_validation.kid_valid(record.payment_reference) or False
                if not valid:
                    raise ValidationError(_("Supplier invoice has invalid KID %s") % (record.payment_reference))
        return super(AccountMove, self).action_post()