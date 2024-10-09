from odoo import models, fields


class WinnerCustomer(models.Model):
    _name = 'winner.customer'
    _description = 'winner.customer'

    partner_id = fields.Many2one('res.partner', string='Forhandler')
    customer_number = fields.Char('Kundenr')  # expecting company_id/customer_no, as sent from Trunk
    pricelist_id = fields.Many2one('product.pricelist', 'Prisliste')

    _sql_constraints = [
        ('unique_customer_number_pricelist_id', 'unique(customer_number, pricelist_id)', 'Kombinasjonen kundenr og prisliste må være unik')
    ]
