from odoo import models, fields, api, _


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    from_analytic_account = fields.Boolean(default=False, required=False)

    # override compute method of account analytic id to include exhibition account
    # this method is not getting called
    @api.depends('product_id', 'date_order', 'order_id.exhibit_analytic_account_id')
    def _compute_account_analytic_id(self):
        for rec in self:
            if rec.display_type not in ['line_section', 'line_note']:
                default_analytic_account = rec.env['account.analytic.default'].sudo().account_get(
                    product_id=rec.product_id.id,
                    partner_id=rec.order_id.partner_id.id,
                    user_id=rec.env.uid,
                    date=rec.date_order,
                    company_id=rec.company_id.id,
                )
                rec.account_analytic_id = rec.order_id.exhibit_analytic_account_id or default_analytic_account.analytic_id
