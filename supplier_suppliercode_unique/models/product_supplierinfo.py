from odoo import models, api, _
from odoo.exceptions import ValidationError


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.constrains('product_code', 'partner_id')
    def _check_supplier_suppliercode_unique(self):
        for supplierinfo in self:
            # For intercompany purchases it is allowed to have duplicate supplier + suppliercode for the production company, but not in production
            if supplierinfo.product_code and supplierinfo.partner_id and supplierinfo.partner_id.id != self.env['res.company'].search([('production', '=', True)], limit=1).partner_id.id and not supplierinfo.partner_id.name.startswith('*Mangler'):
                other_supplierinfos = self.env['product.supplierinfo'].search([('partner_id', '=', supplierinfo.partner_id.id), ('product_code', '=', supplierinfo.product_code), ('company_id', '=', supplierinfo.company_id.id), ('product_tmpl_id', '!=', supplierinfo.product_tmpl_id.id)])
                if len(other_supplierinfos) > 1 or (other_supplierinfos and other_supplierinfos.id != supplierinfo.id):
                    raise ValidationError(_(f'The referenced supplier + suppliercode combination already exists, and must be unique. Supplier: {supplierinfo.partner_id.name} product code: {supplierinfo.product_code}'))

    @api.constrains('winner_product_code', 'partner_id')
    def _check_supplier_winnercode_unique(self):
        for supplierinfo in self:
            # For intercompany purchases it is allowed to have duplicate supplier + winnercode for the production company, but not in production
            if supplierinfo.winner_product_code and supplierinfo.partner_id and supplierinfo.partner_id.id != self.env['res.company'].search([('production', '=', True)], limit=1).partner_id.id and not supplierinfo.partner_id.name.startswith('*Mangler'):
                other_supplierinfos = self.env['product.supplierinfo'].search([('partner_id', '=', supplierinfo.partner_id.id), ('product_code', '=', supplierinfo.winner_product_code), ('company_id', '=', supplierinfo.company_id.id), ('product_tmpl_id', '!=', supplierinfo.product_tmpl_id.id)])
                if len(other_supplierinfos) > 1 or (other_supplierinfos and other_supplierinfos.id != supplierinfo.id):
                    raise ValidationError(_(f'The referenced supplier + winnercode combination already exists, and must be unique. Supplier: {supplierinfo.partner_id.name} product code: {supplierinfo.winner_product_code}'))
