from odoo import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    product_type_id = fields.Many2one('product.type', readonly=True, store=True)
    order_type = fields.Selection(selection=[
        ('standard', 'Standard'),
        ('builder', 'Builder'),
        ('project', 'Project'),
        ('exhibit', 'Exhibition'),
        ('campaign', 'Campaign')
    ], string="Order Type", readonly=True)

    builder_partner_id = fields.Many2one( 'res.partner', readonly=True, store=True, string="Proff partner" )
    developer_id = fields.Many2one( 'res.partner', readonly=True, store=True, string="Utbygger" )
    sales_project_id = fields.Many2one( 'sales.projects', readonly=True, store=True, string="Salgsprosjekt" )
    builder_agreement_situation = fields.Selection([
        ('builder_direct', 'Builder buys directly'),
        ('referral', 'Referral'),
        ('optional_customer', 'Optional customer')
    ], string="Avtalesituasjon", readonly=True)
    product_brand_id = fields.Many2one('akustikken.product.brand', string='Brand', readonly=True)
    store_name = fields.Char(string="Butikk", readonly=True)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", move.order_type, move.product_type_id, move.builder_partner_id, sales_projects.developer_id, move.sales_project_id, move.builder_agreement_situation, template.product_brand_id, move.store_name "

    def _from(self):
        return super()._from() + " LEFT JOIN sales_projects ON sales_projects.id = move.sales_project_id"
