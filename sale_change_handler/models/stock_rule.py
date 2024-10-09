from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        # group id is replenishment group, that is used to group purchase that relates to sale orders
        if partner.order_changes_should_be_synchronized and values.get('group_id') and values.get('group_id').name.startswith('SF'):
            # the replacement of "origin" here is to differentiate orders of stock products and MTO
            domain = tuple(filter(lambda dom: dom[0] not in ['state', 'user_id', 'origin'], domain)) \
                     + (('state', 'not in', ('done', 'cancel')),) \
                     + (('origin', 'ilike', 'SF%'),)
        return domain
