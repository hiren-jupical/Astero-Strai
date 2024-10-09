from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    stock_level = fields.Float()
    # estimated_restock_date = fields.Date()
    deprecated = fields.Boolean()

    vendor_stock_control = fields.Boolean(related='product_tmpl_id.vendor_stock_control', readonly=True, store=False)
