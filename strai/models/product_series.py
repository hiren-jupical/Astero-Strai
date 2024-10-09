from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ProductSeries(models.Model):
    _name = 'akustikken.product.series'
    _description = 'Products Series'

    name = fields.Char("Name", translate=True)
    product_brand_id = fields.Many2one("akustikken.product.brand", "Product Brand")
