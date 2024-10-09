# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Pulls catalogue_price for lines from PO to multicompany SO
    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        res = super(PurchaseOrder, self)._prepare_sale_order_line_data(line, company)
        reverse_pricelist = self.check_reverse_pricelist(res['product_id'], res['product_uom_qty'])
        if reverse_pricelist and 0 < line.strai_discount < 100:
            undiscounted_price = line.price_unit / (1 - line.strai_discount / 100)
        else:
            undiscounted_price = line.price_unit
        price = line.catalogue_price if not reverse_pricelist else undiscounted_price
        res.update({
            'catalogue_price': line.catalogue_price,
            'price_unit': price,
            'discount': line.strai_discount,
            'position': line.position,
            'original_so_line_id': line.so_line_id,
            'winner_catalogue_id': line.winner_catalogue_id.id,
        })
        return res

    # POSSIBLE PROBLEM - Discount calculation is no longer based on unit price. Maybe this check is irrelevant now??
    # Used for checking if the discount is less than zero. If that is true, it means that the catalogue price should not be inserted into unit price on the multicompany sale order,
    # as that will cause a wrong price calculation because the discount(which is also sent to the multicomapny sale order) is based on the unit price.
    def check_reverse_pricelist(self, product, product_qty):
        pricelist = False
        external_vendor = False
        company = self.env['res.company']._find_company_from_partner(self.partner_id.id)
        if not company:
            external_vendor = True
            company = self.company_id
        if self.order_type == 'builder':
            pricelist = self.builder_partner_id.with_company(company).internal_pricelist_id
        if self.order_type in ['standard', 'exhibit']:
            pricelist = self.env['product.pricelist'].sudo().search([('company_id', '=', company.id), ('order_type', '=', self.order_type)], limit=1)
        if self.order_type == 'campaign' and self.price_campaign_id:
            pricelist = self.price_campaign_id.with_company(company).campaign_pricelist_id
        if self.order_type == 'project':
            apartment_count = self.sales_project_id.apartment_count
            if apartment_count >= 10:
                pricelist = self.env['product.pricelist'].sudo().search([('company_id', '=', company.id), ('order_type', '=', self.order_type)], limit=1)
            if apartment_count < 10:
                pricelist = self.sales_project_id.developer_id.with_company(company).internal_pricelist_id
                if self.sales_project_id:
                    if not pricelist:
                        raise UserError(_("There is no pricelist attached to the developer for the chosen project %s") % self.sales_project_id.name)
        if external_vendor and pricelist:
            if pricelist.purchase_pricelist_id:
                pricelist = pricelist.purchase_pricelist_id
        product_id = self.env['product.product'].browse(product)
        discount, rule_is_purchase_based = self.env['purchase.order.line']._get_discount(pricelist, self.company_id, product_qty, product_id)
        return True if discount and discount < 0 else False
