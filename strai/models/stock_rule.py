from odoo import api, models, fields
import logging
from odoo.tools import float_compare
from collections import defaultdict
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import groupby
from dateutil.relativedelta import relativedelta
from odoo.addons.stock.models.stock_rule import ProcurementException




_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _get_procurements_to_merge(self, procurements):
        individual_procurements = []
        for proc in procurements:
            if any([supplier.is_mto for supplier in proc.product_id.seller_ids.mapped('partner_id')]) \
                    and any([rule.group_propagation_option == 'propagate' for rule in proc.product_id.route_ids.mapped('rule_ids')]):
                individual_procurements.append(proc)
        procurements = [proc for proc in procurements if proc not in individual_procurements]
        if procurements:
            res = super(StockRule, self)._get_procurements_to_merge(procurements)
            if individual_procurements:
                res.extend([[proc] for proc in individual_procurements])
            return res
        return [[proc] for proc in individual_procurements]

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super(StockRule, self)._prepare_purchase_order(company_id, origins, values)
        order_type = values[0].get('order_type')
        if order_type:
            res['order_type'] = order_type
        builder_id = values[0].get('builder_partner_id')
        if builder_id:
            res['builder_partner_id'] = builder_id
        campaign = values[0].get('campaign_id')
        if campaign:
            res['campaign_id'] = campaign
        warranty = values[0].get('warranty_identification')
        if warranty:
            res['warranty_identification'] = warranty
        tags = values[0].get('tag_ids')
        if tags:
            res['tag_ids'] = tags
        return res

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        # handle orders to stock, do not append stock products to existing MTO purchases
        if not (values.get('group_id') and values.get('group_id').name.startswith('SF')):
            domain += (('origin', 'not ilike', 'SF%'),)

        # when a purchase is made through replenishment, it uses the selected warehouse for domain
        # this will be overridden to the specified warehouse on the contact. Adjusting the domain accordingly
        if partner.picking_type_id and partner.picking_type_id.id:
            domain = tuple(filter(lambda dom: dom[0] not in ['picking_type_id'], domain)) \
                + (('picking_type_id', '=', partner.picking_type_id.id),)

        return domain


############################### Created Virtual PO for Calculate Contribution Margin ##########################################################

    @api.model
    def _run_so_buy_amt(self, procurements):
        procurements_by_po_domain = defaultdict(list)
        errors = []
        so_po = False
        total_amount_untaxed = 0.0
        for procurement, rule in procurements:
            
            procurement_date_planned = fields.Datetime.from_string(procurement.values['date_planned'])

            supplier = False
            if procurement.values.get('supplierinfo_id'):
                supplier = procurement.values['supplierinfo_id']
            elif procurement.values.get('orderpoint_id') and procurement.values['orderpoint_id'].supplier_id:
                supplier = procurement.values['orderpoint_id'].supplier_id
            else:
                supplier = procurement.product_id.with_company(procurement.company_id.id)._select_seller(
                    partner_id=procurement.values.get("supplierinfo_name") or (procurement.values.get("group_id") and procurement.values.get("group_id").partner_id),
                    quantity=procurement.product_qty,
                    date=max(procurement_date_planned.date(), fields.Date.today()),
                    uom_id=procurement.product_uom)

            supplier = supplier or procurement.product_id._prepare_sellers(False).filtered(
                lambda s: not s.company_id or s.company_id == procurement.company_id
            )[:1]

            if not supplier:
                msg = _('There is no matching vendor price to generate the purchase order for product %s (no vendor defined, minimum quantity not reached, dates not valid, ...). Go on the product form and complete the list of vendors.', procurement.product_id.display_name)
                errors.append((procurement, msg))

            partner = supplier.partner_id
            procurement.values['supplier'] = supplier
            procurement.values['propagate_cancel'] = rule.propagate_cancel

            domain = rule._make_po_get_domain(procurement.company_id, procurement.values, partner)
            procurements_by_po_domain[domain].append((procurement, rule))

        if errors:
            raise ProcurementException(errors)

        for domain, procurements_rules in procurements_by_po_domain.items():

            procurements, rules = zip(*procurements_rules)

            origins = set([p.origin for p in procurements])
            po = self.env['purchase.order'].sudo().search([dom for dom in domain], limit=1)
            company_id = procurements[0].company_id
            if not po:
                positive_values = [p.values for p in procurements if float_compare(p.product_qty, 0.0, precision_rounding=p.product_uom.rounding) >= 0]
                if positive_values:
                    vals = rules[0]._prepare_purchase_order(company_id, origins, positive_values)
                    if self.env.context.get('so_id'):
                        so_po = self.env['purchase.order'].with_company(company_id).with_user(SUPERUSER_ID).new(vals)
            else:
                if po.origin:
                    missing_origins = origins - set(po.origin.split(', '))
                    if missing_origins:
                        po.write({'origin': po.origin + ', ' + ', '.join(missing_origins)})
                else:
                    po.write({'origin': ', '.join(origins)})

            procurements_to_merge = self._get_procurements_to_merge(procurements)
            procurements = self._merge_procurements(procurements_to_merge)

            po_lines_by_product = {}
            grouped_po_lines = groupby(po.order_line.filtered(lambda l: not l.display_type and l.product_uom == l.product_id.uom_po_id), key=lambda l: l.product_id.id)
            for product, po_lines in grouped_po_lines:
                po_lines_by_product[product] = self.env['purchase.order.line'].concat(*po_lines)
            po_line_values = []
            po_line_new_values = []
            for procurement in procurements:
                po_lines = po_lines_by_product.get(procurement.product_id.id, self.env['purchase.order.line'])
                po_line = po_lines._find_candidate(*procurement)

                if po_line:
                    vals = self._update_purchase_order_line(procurement.product_id,
                        procurement.product_qty, procurement.product_uom, company_id,
                        procurement.values, po_line)
                    po_line.sudo().write(vals)
                else:
                    if float_compare(procurement.product_qty, 0, precision_rounding=procurement.product_uom.rounding) <= 0:
                        continue

                    partner = procurement.values['supplier'].partner_id
                    if self.env.context.get('so_id'):
                        po_line_new_values.append(self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
                        procurement.product_id, procurement.product_qty,
                        procurement.product_uom, procurement.company_id,
                        procurement.values, so_po))

                    order_date_planned = procurement.values['date_planned'] - relativedelta(
                        days=procurement.values['supplier'].delay)
            if self.env.context.get('so_id') and so_po:
                so_id = self.env.context['so_id']
                vi_so_line_id = self.env.context['vi_so_line_id']
                po_line = po_line_new_values[0]
                po_line.update({'sale_line_id':vi_so_line_id})
                so_ln_po = self.env['purchase.order.line'].sudo().new(po_line)
                so_rec = self.env['sale.order'].browse(so_id.id)
                if so_rec:
                    so_rec.get_po_vals(so_po)



class ProcurementIntGroup(models.Model):

    _inherit = "procurement.group"

    @api.model
    def run(self, procurements, raise_user_error=True):
        if not self.env.context.get('so_id'):
            return super(ProcurementIntGroup, self).run(procurements, raise_user_error)

        actions_to_run = defaultdict(list)
        procurement_errors = []

        for procurement in procurements:
            procurement.values.setdefault('company_id', procurement.location_id.company_id)
            procurement.values.setdefault('priority', '0')
            procurement.values.setdefault('date_planned', procurement.values.get('date_planned') or fields.Datetime.now())

            if self._skip_procurement(procurement):
                continue

            rule = self._get_rule(procurement.product_id, procurement.location_id, procurement.values)
            
            if not rule:
                error = _(
                    'No rule has been found to replenish %r in %r.\nVerify the routes configuration on the product.',
                    procurement.product_id.display_name, procurement.location_id.display_name)
                procurement_errors.append((procurement, error))
            else:
                action = 'pull' if rule.action == 'pull_push' else rule.action
                actions_to_run[action].append((procurement, rule))

        stock_rule_env = self.env['stock.rule']
        for action, action_procurements in actions_to_run.items():
            getattr(stock_rule_env, '_run_%s' % 'so_buy_amt')(action_procurements)
        return True


#########################################################################################################################################################