# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    # copy / paste from standard, no changes. Does not work to not include this for some reason
    def get_product_price_rule(self, product, quantity, date=False, uom=False):
        """ For a given pricelist, return price and rule for a given product """
        self.ensure_one()
        return self._compute_price_rule(product, quantity, uom=uom, date=date)[product.id]

    # In order to make pricelists work with brands & series, it is necessary to override the entire
    # _compute_price_rule method. The original can be found at
    # https://github.com/odoo/odoo/blob/12.0/addons/product/models/product_pricelist.py#L99 I will mark the parts
    # that have been overwritten with OVERRIDE
    def _compute_price_rule(
        self, products, quantity, currency=None, uom=None, date=False, compute_price=True,
        **kwargs
    ):
        """ Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given pricelist}

        :param products: recordset of products (product.product/product.template)
        :param float quantity: quantity of products requested (in given uom)
        :param uom: unit of measure (uom.uom record)
            If not specified, prices returned are expressed in product uoms
        :param date: date to use for price computation and currency conversions
        :type date: date or datetime

        :returns: product_id: (price, pricelist_rule)
        :rtype: dict
        """
        self and self.ensure_one()  # self is at most one record

        currency = currency or self.currency_id or self.env.company.currency_id
        currency.ensure_one()

        if not products:
            return {}

        if not date:
            # Used to fetch pricelist rules and currency rates
            date = fields.Datetime.now()
        if self:
            brand_ids = self._get_product_brands(products)
            series_ids = self._get_product_series(products)

            self._cr.execute(
                'SELECT item.id '
                'FROM product_pricelist_item AS item '
                'LEFT JOIN product_category AS categ '
                'ON item.categ_id = categ.id '
                'LEFT JOIN akustikken_product_brand AS brand '
                'ON item.brand_id = brand.id '
                'LEFT JOIN akustikken_product_series AS series '
                'ON item.series_id = series.id '
                'WHERE (item.product_id IS NULL OR item.product_id = any(%s)) '
                'AND (item.brand_id IS NULL OR item.brand_id = any(%s)) '
                'AND (item.series_id IS NULL OR item.series_id = any(%s)) '
                'AND (item.pricelist_id = %s) '
                'AND (item.date_start IS NULL OR item.date_start<=%s) '
                'AND (item.date_end IS NULL OR item.date_end>=%s)'
                ' ORDER BY CASE item.applied_on '
                '           when \'0_product_variant\' then 1'
                '           when \'1_product\' then 2'
                '           when \'5_series\' then 3'
                '           when \'4_brands\' then 4'
                '           when \'3_global\' then 5'
                '           else 99 '
                'END, item.brand_id, item.series_id, item.min_quantity desc, categ.complete_name desc, item.id desc',
                (products.ids, brand_ids, series_ids, self.id, date, date))
            # NOTE: if you change `order by` on that query, make sure it matches
            # _order from model to avoid inconstencies and undeterministic issues.

            rule_ids = [x[0] for x in self._cr.fetchall()]
            rules = self.env['product.pricelist.item'].browse(rule_ids)
        else:
            rules = self._get_applicable_rules(products, date, **kwargs)

        results = {}
        for product in products:
            suitable_rule = self.env['product.pricelist.item']

            product_uom = product.uom_id
            target_uom = uom or product_uom  # If no uom is specified, fall back on the product uom

            # Compute quantity in product uom because pricelist rules are specified
            # w.r.t product default UoM (min_quantity, price_surchage, ...)
            if target_uom != product_uom:
                qty_in_product_uom = target_uom._compute_quantity(
                    quantity, product_uom, raise_if_failure=False
                )
            else:
                qty_in_product_uom = quantity

            for rule in rules:
                if rule._is_applicable_for(product, qty_in_product_uom):
                    suitable_rule = rule
                    break

            if compute_price:
                price = suitable_rule._compute_price(
                    product, quantity, target_uom, date=date, currency=currency)
            else:
                # Skip price computation when only the rule is requested.
                price = 0.0
            results[product.id] = (price, suitable_rule.id)

        return results

    def _get_product_series(self, products):
        series_ids = {}
        for p in products:
            if p.product_tmpl_id.product_series_id:
                series_ids[p.product_tmpl_id.product_series_id.id] = True
        return list(series_ids)

    def _get_product_brands(self, products):
        brand_ids = {}
        for p in products:
            brand = p.product_tmpl_id.product_brand_id
            if brand:
                brand_ids[brand.id] = True
        brand_ids = list(brand_ids)
        return brand_ids
