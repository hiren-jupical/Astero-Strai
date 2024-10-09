from odoo import fields, models, _
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    order_type = fields.Selection(selection=[
        ('project', 'Project'),
        ('exhibit', 'Exhibition'),
        ('standard', 'Standard'),
        ('builder', 'Builder'),
        ('campaign', 'Campaign'),
        ('purchase', 'Purchase')
    ], string="Order Type")
    is_production = fields.Boolean(compute='compute_is_production')

    purchase_pricelist_id = fields.Many2one('product.pricelist', domain="[('order_type', '=', 'purchase')]")
    builder_discount_matrix = fields.One2many('product.pricelist.builder.discount.matrix', 'product_pricelist_id', string="Rabattmatrise")
    available_for = fields.Selection([
        ('proff', 'Proff'),
    ], required=False, default=False, string="Tilgjengelig for")

    def copy(self, default=None):
        res = super().copy(default)
        for rec in res:
            rec.order_type = False
        return res

    def write(self, vals):
        for rec in self:
            ordertype = vals.get('order_type') or False
            if ordertype and ordertype in ['standard', 'exhibit', 'project']:
                other_pricelists = self.env['product.pricelist'].search([('order_type', '=', ordertype), ('id', '!=', rec.id)])
                if other_pricelists:
                    raise UserError(_('Another pricelist already exists with this order type'))
        return super().write(vals)

    def compute_is_production(self):
        if self.env.company.production:
            self.is_production = True
        else:
            self.is_production = False
