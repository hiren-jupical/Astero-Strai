from odoo import fields, models, api, _


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    winner_product_code = fields.Char('Winner product code', required=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProductSupplierinfo, self).create(vals_list)
        for rec in res:
            no_supplier_record = self.env['product.supplierinfo'].sudo().search([('company_id', '=', rec.company_id.id), ('product_tmpl_id', '=', rec.product_tmpl_id.id), ('product_code', '=', 'no_supplier')], limit=1)
            if not rec.product_code == 'no_supplier' and no_supplier_record:
                no_supplier_record.unlink()
            if not rec.product_code:
                rec.product_code = rec.product_tmpl_id.default_code
        return res
