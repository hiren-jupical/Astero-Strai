# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    strai_discount = fields.Float(compute='_compute_strai_discount', store=True, readonly=False)

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier, po):
        """ Extends standard Odoo method to include custom pricing, found in pricelists in main company (strai kjøkken)
            Considers order type and handles reverse discounts. (Discounts based on purchase price in main company, minus a fixed percentage from the pricelist)
            Price discounts are found in main company pricelists from brand or brand and series.
        """
        if product_id != False:
            """Apply the discount to the created purchase order"""
            res = super()._prepare_purchase_order_line(
                product_id, product_qty, product_uom, company_id, supplier, po
            )
            pricelist = False
            pricelist_item = False
            external_vendor = False
            company = self.env['res.company']._find_company_from_partner(po.partner_id.id)
            production_company = self.env['res.company'].sudo().search([('production', '=', True)])
            discount = 0
            if not company:
                external_vendor = True
                # company = self.company_id or company_id
            if po.order_type == 'builder':
                pricelist = po.builder_partner_id.with_company(production_company).sudo().internal_pricelist_id
            if po.order_type in ['standard', 'exhibit']:
                order_type = po.order_type
                pricelist = self.env['product.pricelist'].sudo().search([('company_id', '=', production_company.id), ('order_type', '=', order_type)], limit=1)
            if po.order_type == 'campaign' and po.price_campaign_id:
                pricelist = po.price_campaign_id.with_company(production_company).sudo().campaign_pricelist_id
            if po.order_type == 'project':
                apartment_count = po.sales_project_id.apartment_count
                if apartment_count >= 10:
                    pricelist = po.env['product.pricelist'].sudo().search([('company_id', '=', production_company.id), ('order_type', '=', po.order_type)], limit=1)
                if apartment_count < 10:
                    pricelist = po.sales_project_id.developer_id.with_company(production_company).sudo().internal_pricelist_id
                    if po.sales_project_id:
                        if not pricelist:
                            raise UserError(_("There is no pricelist attached to the developer for the chosen project %s") % po.sales_project_id.name)
            if pricelist:
                price, rule_id = pricelist.get_product_price_rule(product_id.with_company(production_company).sudo(), product_qty)
                if rule_id:
                    pricelist_item = self.env['product.pricelist.item'].browse(rule_id)
            if external_vendor and pricelist:
                if pricelist.purchase_pricelist_id:
                    pricelist = pricelist.purchase_pricelist_id
                    # res.update(self._prepare_purchase_order_line_from_so_line(po, product_id))

            rule_is_purchase_based = False
            if pricelist:
                discount, rule_is_purchase_based = self._get_discount(pricelist, production_company, product_qty, product_id)
            res.update(self._prepare_purchase_order_line_discount(discount, product_id, po))
            if rule_is_purchase_based:
                res.update({'rule_base_purchase_price': True})
            # if discount == 0:
            #     if pricelist:
            return res

    # Finds out how the price of 100 would be changed from the pricelist discount(s) and then converts the new_price to a percentage to return.
    # If pricelist is based on a pricelist, recursion occurs.
    def _get_discount(self, pricelist, company, product_qty, product):
        results = (0, False)
        rule_is_purchase_based = False
        discount = 0
        discount_inline = 0
        if product.id != False and pricelist:
            if self.display_type not in ['line_section', 'line_note']:
                price, rule_id = pricelist.get_product_price_rule(product.with_company(company).sudo(), product_qty)
                if rule_id:
                    rule = self.env['product.pricelist.item'].browse(rule_id)
                    if rule.base == 'pricelist':
                        discount_inline, rule_is_purchase_based = self._get_discount(rule.base_pricelist_id, company, product_qty, product)
                    new_price = (((100 - rule.price_discount) / 100) * 100) * ((100 - discount_inline) / 100) if rule.base == 'pricelist' else (((100 - rule.price_discount) / 100) * 100)
                    discount = ((100 - new_price) / 100) * 100 if not new_price == 0.0 else 0.0
                    if rule.base == 'purchase_price':
                        rule_is_purchase_based = True
            results = (discount, rule_is_purchase_based)
        return results

    @api.model
    def _prepare_purchase_order_line_discount(self, discount, product_id, po):
        if product_id:
            if not discount:
                return {}
            if discount < 0:
                production_company = self.env['res.company'].sudo().search([('production', '=', True)])
                vendor_price = False
                supplier_info_recs = self.env['product.supplierinfo'].sudo().search([('company_id', '=', production_company.id), ('product_tmpl_id', '=', product_id.product_tmpl_id.id)])
                for vendor in supplier_info_recs:
                    if vendor.price != 0:
                        vendor_price = vendor.price
                        break
                if vendor_price:
                    reverse_discount = self._calculate_reverse_discount(vendor_price, discount, po, product_id)
                    return {"strai_discount": reverse_discount,
                            "activate_onchange_price": True,
                            "vendor_price": vendor_price,
                            "base_vendor_discount": discount}
            return {"strai_discount": discount}

    # Calculates discount based on surcharge pricelists, where the stores must not be able to see the surcharge.
    # Therefore, the discount is calculated as the vendor price + the percent surcharge, as a percent of the price_unit
    @api.model
    def _calculate_reverse_discount(self, vendor_price, discount, po, product_id, onchange_sale_price=False):
        if product_id:
            reverse_discount = 0.0
            price_dict = self._prepare_purchase_order_line_from_so_line(po, product_id)
            if price_dict:
                sale_price = max(price_dict["catalogue_price"], price_dict["price_unit"]) if not onchange_sale_price else onchange_sale_price
                vendor_pricelist_price = vendor_price * (((discount * -1) / 100) + 1)
                reverse_discount = ((sale_price - vendor_pricelist_price) / sale_price) * 100 if sale_price != 0 else 0
            return reverse_discount

    @api.depends('price_unit', 'price_before_discount')
    def _compute_strai_discount(self):
        for line in self:
            line.strai_discount = ((line.price_before_discount - line.price_unit) / line.price_before_discount) * 100.0 if line.price_before_discount > 0.0 and line.strai_discount == 0.0 else line.strai_discount or 0.0
            if self.env.context.get('default_price_unit_changed') and line.strai_discount <= 0.0:
                line.strai_discount = 0.0

    @api.onchange('strai_discount')
    @api.depends('strai_discount')
    def _onchange_discount(self):
        for line in self:
            if not line.price_changed_manually:
                # field created after go-live. Set field on demand to avoid errors
                if line.price_before_discount == 0.0:
                    line.price_before_discount = line.price_unit
                line.price_unit = line.price_before_discount * (1 - line.strai_discount / 100.0)
            line.price_changed_manually = False

    @api.onchange('price_unit')
    @api.depends('price_unit')
    def _onchange_price_unit(self):
        for line in self:
            # field created after go-live. Set field on demand to avoid errors
            if self.env.context.get('default_price_unit_changed') and line.strai_discount != 0.0:
                line.strai_discount = 0.0
            if (line.price_before_discount == 0.0) or (self.env.context.get('default_price_unit_changed') and line.strai_discount == 0.0):
                line.price_before_discount = line.price_unit
            line.price_changed_manually = True

    @api.depends('sale_line_id.price_unit', 'sale_line_id.catalogue_price')
    def update_price_before_discount(self):
        for line in self:
            line.price_before_discount = max(line.sale_line_id.price_unit, line.sale_line_id.catalogue_price)
            line.price_unit = line.price_before_discount * (1 - line.strai_discount / 100.0)

    # override standard function purchase/models/purchase
    # gets called when product qty on sale order line is changed, and recalculate price by-passing price list structure
    # check if the price is about to be re-calculated, and stop it if it is
    @api.depends('product_qty', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        origin_lines = [(line.id, line.price_unit, line.strai_discount) for line in self]
        super()._compute_price_unit_and_date_planned_and_name()
        for line in self:
            # StopIterationException when using "next" instead of list on new items
            orig_line = list(filter(lambda x: x[0] == line.id, origin_lines))
            if orig_line and len(orig_line) == 1 and len(orig_line[0]) == 3:
                orig_line_id, orig_line_price_unit, orig_line_discount = orig_line[0]
                if line.sale_line_id and line.price_unit != orig_line_price_unit:
                    line.price_unit = orig_line_price_unit
                    line.strai_discount = orig_line_discount
