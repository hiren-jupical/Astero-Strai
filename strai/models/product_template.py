from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one("akustikken.product.brand", "Product Brand")
    product_series_id = fields.Many2one("akustikken.product.series", "Product Series", ondelete="restrict", domain="[('product_brand_id', '=', product_brand_id)]")

    created_by_trunk = fields.Boolean(default=False)

    # By adding a purchase_price field (exact name as the pricelist selection field value),
    # standard Odoo pricelist calculcationscan find the field directly, without having to override methods
    purchase_price = fields.Monetary(compute="_compute_purchase_price")

    service_to_purchase = fields.Boolean("Subcontract Service", company_dependent=True, help="If ticked, each time you sell this product through a SO, a RfQ is automatically created to buy the product. Tip: don't forget to set a vendor on the product.")

    @api.depends_context('company')
    @api.depends('seller_ids')
    def _compute_purchase_price(self):
        for r in self:
            if r.seller_ids:
                sellers = r.seller_ids.filtered(lambda s: (s.company_id == False or s.company_id.id == self.env.company.id) and (s.date_end == False or s.date_end > fields.Date.today()) and (s.date_start == False or s.date_start <= fields.Date.today()))
                if sellers:
                    r.purchase_price = sellers.sorted(lambda s: s.price)[0].price if len(sellers) > 1 else sellers.price
                else:
                    r.purchase_price = 0.0
            else:
                r.purchase_price = 0.0
