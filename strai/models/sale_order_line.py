from odoo import api, fields, models, _
import logging
from odoo.tools import float_compare
from collections import defaultdict
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import groupby
from dateutil.relativedelta import relativedelta



_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    position_added_to_po = fields.Boolean()

    # sale_line_name_to_purchase_line is used in create method on puchase_order_line
    # This is used for checking if a line has been modified
    # copy=False - does so that when we copy a SO, i won't copy the value from it
    sale_line_name_to_purchase_line = fields.Boolean(default=False, copy=False)

    order_type = fields.Selection(string="Order Type", related='order_id.order_type')
    catalogue_price = fields.Monetary()
    purchase_line_id = fields.Char(copy=False)

    position = fields.Integer(string="pos", help="Winner line number")
    no_supplier_warning = fields.Boolean(compute='compute_supplier_warning')

    original_so_line_id = fields.Char()

    winner_catalogue_id = fields.Many2one('winner.catalogue', string="Winner catalogue", required=False)

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        res.update(
            {
                'order_type': self.order_type,
                'name': self.name,
                'builder_partner_id': self.order_id.builder_partner_id.id,
                'price_campaign_id': self.order_id.price_campaign_id.id,
                'project_id': self.order_id.project_id.id,
                'warranty_identification': self.order_id.warranty_identification,
                'tag_ids': [(6, 0, [t.id for t in self.order_id.tag_ids])],
                'original_sale_order_line': self.original_so_line_id
            })
        return res

    # Overwrite method to implement custom discount from pricelist logic.
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_discount(self):
        for line in self:
            if not (line.product_id and line.product_uom and
                    line.order_id.partner_id and line.order_id.pricelist_id and
                    line.order_id.pricelist_id.discount_policy == 'without_discount' and
                    line.env.user.has_group('product.group_discount_per_so_line')):
                return
            line.discount = 0.0
            product_context = dict(line.env.context, partner_id=line.order_id.partner_id.id, date=line.order_id.date_order,
                                   uom=line.product_uom.id)
            price, rule_id = line.order_id.pricelist_id.with_context(product_context)._get_product_price_rule(
                line.product_id, line.product_uom_qty or 1.0)
            rule = False
            # Overwrite start: Calculation price based on catalogue price instead of list price.
            if rule_id:
                rule = line.env['product.pricelist.item'].search([('id', '=', rule_id)])
            if rule and price == 0:
                price = line.catalogue_price * (1 - (rule.price_discount / 100))
            # new_list_price, currency = line.with_context(product_context)._get_real_price_currency(product, rule_id, line.product_uom_qty, line.product_uom, line.order_id.pricelist_id.id)
            new_list_price = line._get_pricelist_price_before_discount()
            if rule and new_list_price == 0:
                new_list_price = line.catalogue_price
            if rule and price > 1:
                new_list_price = line.price_unit
            # Overwrite end
            if new_list_price != 0:
                # check for reverse discount
                discount = (new_list_price - price) / new_list_price * 100
                discount2 = line._get_discount(line.order_id.pricelist_id)
                if discount2 < 0.0:
                    line.discount = discount
                else:
                    line.discount = discount2

    def _get_discount(self, pricelist_id):
        product = self.product_id
        company = self.order_id.company_id
        discount = 0
        if product.id != False:
            if self.display_type != 'line_section':
                price, rule_id = pricelist_id._get_product_price_rule(product.with_company(company),
                                                                     self.product_uom_qty)
                # rule = self.env['product.pricelist.item'].browse(rule_id)
                if rule_id:
                    rule = self.env['product.pricelist.item'].browse(rule_id)
                    new_price = (((100 - rule.price_discount) / 100) * 100) * ((100 - self._get_discount(
                        rule.base_pricelist_id)) / 100) if rule.base == 'pricelist' else (
                                ((100 - rule.price_discount) / 100) * 100)
                    discount = ((100 - new_price) / 100) * 100 if not new_price == 0.0 else 0.0
        return discount

    # Overwrite entire method. Prices should not be set as list price when product_uom is changed. It also affected the button "update pricelist", which it should not.
    # We use the custom field "catalogue_price" instead of list price.
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        return

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res['position'] = self.position
        return res

    @api.depends('product_id')
    def compute_supplier_warning(self):
        for line in self:
            if line.order_id.is_production and line.product_id and line.product_id.seller_ids and \
                    line.product_id.seller_ids[0].partner_id.ref == 'no_supplier' and line.product_id.type == 'product':
                line.no_supplier_warning = True
            else:
                line.no_supplier_warning = False

    def action_supplier_warning(self):
        return {
            'name': _(''),
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'product.supplierinfo',
            'res_id': self.product_id.seller_ids[0].id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # override base function from sale_purchase/sale_order/sale_order_line
    def _purchase_service_generation(self):
        """ Create a Purchase from the sale line for services. If the SO line already created a PO, it
            will create a second one.
        """
        sale_line_purchase_map = {}
        for line in self:
            # Do not regenerate PO line if the SO line has already created one in the past (SO cancel/reconfirmation case)
            if line.product_id.service_to_purchase:
                result = line._purchase_service_create()
                sale_line_purchase_map.update(result)
        return sale_line_purchase_map

    # override base function from sale_purchase_inter_company_rules
    def _purchase_service_create(self, quantity=False):
        line_to_purchase = set()
        overriden_lines = []
        for line in self:
            if line.product_id.service_to_purchase:
                # set this to False to satisfy requirements in sale_purchase_inter_company_rules/models/sale_order/_purchase_service_create
                # put it back afterwards!
                if line.order_id.auto_generated:
                    overriden_lines += [line]
                    line.order_id.auto_generated = False
                line_to_purchase.add(line.id)
        line_to_purchase = self.env['sale.order.line'].browse(list(line_to_purchase))
        res = super(SaleOrderLine, line_to_purchase)._purchase_service_create(quantity=quantity)
        # put back value to original state
        for line in overriden_lines:
            line.order_id.auto_generated = True
        return res

    # override standard to avoid getting sale price from product when imported from Winner
    # avoid overriding manual set prices with sale prices from product
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            if line.catalogue_price or (line.price_unit > 0.0 and line.catalogue_price == 0.0 and line.price_unit != line.product_id.lst_price):
                return
        super()._compute_price_unit()


############################### Created Virtual PO for Calculate Contribution Margin ##########################################################


    def so_line_get_po_val(self,previous_product_uom_qty=False):

        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(line._create_procurement(product_qty, procurement_uom, values))

        if procurements and self.order_id:
            self.env['procurement.group'].with_context(so_id=self.order_id,vi_so_line_id=self.id).run(procurements)

#########################################################################################################################################################