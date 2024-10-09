from odoo import fields, models


class AnalyticExhibitionLineMissing(models.TransientModel):
    _name = 'analytic.exhibition.line.missing'
    _description = 'Analytic Exhibition Line Missing'

    wizard_id = fields.Many2one('analytic.exhibition.lines')
    product_id = fields.Many2one('product.product')
    name = fields.Char()
    unit_amount = fields.Float()
    chosen_amount = fields.Float()
    analytic_line_id = fields.Many2one('account.analytic.line')
    invoice_id = fields.Many2one('account.move')
