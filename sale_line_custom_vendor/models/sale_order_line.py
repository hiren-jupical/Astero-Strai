from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    change_vendor_possible = fields.Boolean(compute='_compute_change_vendor_possible')
    alternative_vendor = fields.Many2one('product.supplierinfo')
    current_vendor = fields.Many2one('product.supplierinfo', compute='_compute_current_vendor', store=True, readonly=False)

    def action_change_vendor(self):
        wizard = self.env['vendor.wizard'].create({'sale_order_line': self.id})
        return {
            'name': _("Vendor Wizard"),
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'vendor.wizard',
            'res_id': wizard.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.depends('product_id', 'alternative_vendor', 'product_id.seller_ids')
    def _compute_current_vendor(self):
        for line in self:
            if line.order_id.state in ['cancel', 'done']:
                continue

            if line.alternative_vendor:
                line.current_vendor = line.alternative_vendor.id
                continue

            if line.product_id:
                seller = line.product_id.with_company(line.company_id.id)._select_seller(quantity=None)
                if seller:
                    line.current_vendor = seller.id

    @api.depends('product_id', 'product_id.seller_ids')
    def _compute_change_vendor_possible(self):
        for line in self:
            if line.order_id.activate_vendor_pr_line and line.product_id and len(line.product_id.with_company(self.env.company.id).seller_ids) > 1:
                line.change_vendor_possible = True
            else:
                line.change_vendor_possible = False
