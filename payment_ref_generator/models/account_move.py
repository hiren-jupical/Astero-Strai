from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_invoice_reference_no_invoice(self):
        if self.filtered(lambda l: l.name and l.name.isdigit() and l.move_type in ['out_invoice', 'out_refund']):
            return self._set_kid_mod10()
        return super()._get_invoice_reference_no_invoice()

    def _set_kid_mod10(self):
        self.ensure_one()
        return "%s%s" % (self.name, (10 - (sum([int(n) for n in list("".join([str(int(val) * [
                    2, 1][idx % 2]) for idx, val in enumerate(list(str(self.name))[::-1])]))]) % 10)) % 10)
