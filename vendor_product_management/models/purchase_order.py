from odoo import models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for po in self:
            deprecated_products = []
            for line in po.order_line:
                if line.product_id.product_tmpl_id.deprecated:
                    deprecated_products.append(f'Pos {line.position}: {line.product_id.name}')
            if deprecated_products:
                raise UserError(_('Du har produkter som er utgått i tilbudet ditt. Ta kontakt med innkjøp for erstatningsprodukter. Utgåtte produkter:\n%s') % "\n".join(deprecated_products))
        return super(PurchaseOrder, self).button_confirm()
