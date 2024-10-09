from odoo import fields, models, _


class StraiCampaign(models.Model):
    _name = 'strai.campaign'
    _description = 'Campaign'

    _sql_constraints = [
            ('_campaign_has_name', 'check (name IS NOT NULL)', 'Campaign must have name'),
            ('_campaign_has_pricelist', 'check (campaign_pricelist_id IS NOT NULL)', 'Campaign must have pricelist'),
    ]

    name = fields.Char(string="Campaign", required=True)
    from_date = fields.Date()
    to_date = fields.Date()
    campaign_pricelist_id = fields.Many2one('product.pricelist', required=True)
    campaign_info = fields.Text(string="Comment", help="Comment that will be pushed to SO/PO in the info_accounting (Accounting Comment) field")
    campaign_company_ids = fields.Many2many('res.company', 'campaign_id', string="Available for:", required=True)
    sale_count = fields.Integer(compute='compute_campaign_sale_orders', string="Campaigns Sale Orders")

    def compute_campaign_sale_orders(self):
        sale_orders = self.env['sale.order']
        for campaign in self:
            campaign.sale_count = sale_orders.search_count([('price_campaign_id', '=', campaign.id)])

    def sale_order_view(self):
        return {
            'name': _("Campaigns Sale Orders"),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('price_campaign_id', '=', self.id)]
        }
