from odoo import api, fields, models, _


class StockQuantInherit(models.Model):
    _inherit = 'stock.quant'

    vendor_id = fields.Many2one('res.partner', string='Leverandør', compute='_compute_vendor_stock_quant', store=True)

    @api.depends('product_id', 'product_id.seller_ids', 'product_id.seller_ids.partner_id', 'product_id.seller_ids.sequence', 'product_id.product_tmpl_id.seller_ids', 'product_id.product_tmpl_id.seller_ids.sequence')
    def _compute_vendor_stock_quant(self):
        for quant in self:
            supplier_info_record = self.env['product.supplierinfo'].sudo().search([('product_tmpl_id', '=', quant.product_id.product_tmpl_id.id)], order='sequence asc', limit=1)
            if supplier_info_record:
                quant.vendor_id = supplier_info_record.partner_id.id
