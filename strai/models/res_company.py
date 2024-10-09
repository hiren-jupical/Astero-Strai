from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    production = fields.Boolean(default=False, string='Production Company')

    # This field is used when importing products from Trunk, which have not yet been created and need to be assigned to a route
    product_route_ids = fields.Many2many(
        'stock.route', 'stock_route_company', 'company_id', 'route_id', 'Routes',
        domain=[('product_selectable', '=', True)],
        help="Depending on the modules installed, this will allow you to define the route of the products in this company: whether it will be bought, manufactured, replenished on order, etc.")

    default_payment_term = fields.Many2one('account.payment.term', string='Standard payment term')
    warranty_product_id = fields.Many2one('product.product', string="Complaint product")
    invoice_sender_email = fields.Char(string="Epostavsender faktura")
    pass_through_billing_product_id = fields.Many2one('product.product', string="Viderefaktureringsprodukt")

    @api.model
    def find_company_from_partner(self, partner_id):
        company = self.sudo().search([('partner_id', '=', partner_id.id)], limit=1)
        return company or False
