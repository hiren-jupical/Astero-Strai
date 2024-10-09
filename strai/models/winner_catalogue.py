from odoo import models, fields


class WinnerCatalogue(models.Model):
    _name = 'winner.catalogue'
    _description = 'Winner Catalogue'

    name = fields.Char()
    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True)
    catalogue_name = fields.Char(required=True)
    catalogue_version = fields.Integer(required=True)
    accepted = fields.Boolean(required=True)

    sale_order_line = fields.One2many('sale.order.line', 'winner_catalogue_id', string='Sale order lines')
    purchase_order_line = fields.One2many('purchase.order.line', 'winner_catalogue_id', string='Purchase order lines')

    _sql_constraints = [
        ('unique_supplier_catalogue_name_version', 'unique(supplier_id, catalogue_name, catalogue_version)', 'Supplier catalogue name and version needs to be unique')
    ]
