from odoo import fields, models, api


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    product_type_id = fields.Many2one('product.type', related='move_line_id.move_id.product_type_id', string='Product Type', store=True)
    order_type = fields.Selection(string="Order Type", related='move_line_id.move_id.order_type', store=True)
    # selection=[
    # ('standard', 'Standard'),
    # ('builder', 'Builder'),
    # ('project', 'Project'),
    # ('exhibit', 'Exhibition'),
    # ('campaign', 'Campaign')
    # ],
    categ_id = fields.Many2one('product.category', string='Product Category', related='product_id.categ_id', store=True)

    margin = fields.Monetary(
        'Margin In (%)', group_operator="avg", copy=False,
        readonly=False, store=True, help='This field show the contribution margin at the time of group by with product category')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        groups = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        # hack to calculate margin dynamically
        context = dict(self.env.context or {})
        if context.get('active_model') == 'account.analytic.account':
            for group in groups:
                if group.get('categ_id') and 'margin' in group:
                    group['margin'] = self._get_margin_by_category(context.get('active_id'), group['categ_id'][0])
        return groups

    def _get_margin_by_category(self, analytic_account_id, category_id):
        account = self.env['account.analytic.account'].browse(analytic_account_id)
        analytic_lines = account.exhibit_analytic_line_ids.filtered(lambda l: l.categ_id.id == category_id and l.move_line_id.parent_state == 'posted' and l.move_line_id.move_type in ['out_invoice', 'in_invoice', 'in_refund', 'out_refund'])
        sale_lines = analytic_lines.filtered(lambda l: l.move_line_id.move_type in ['out_invoice', 'out_refund'])
        sales = sum(sale_lines.mapped('amount'))
        amount = sum(analytic_lines.mapped('amount'))
        if sales > 0:
            return amount / sales * 100
        return 0

    @api.model
    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        if self.env.context.get('exclude_zero_line', False):
            domain.append(('unit_amount', '>', 0))
        return super()._read_group(domain, groupby=groupby, aggregates=aggregates, having=having, offset=offset, limit=limit,
                            order=order)
