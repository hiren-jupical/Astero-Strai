from datetime import datetime

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    boml_received = fields.Boolean(string='Received BOML')
    boml_last_updated = fields.Datetime(string='BOML last updated')

    def update_boml(self, order_data):
        order = order_data['order']

        products = self.process_articles(order['articles'])

        self.update_sale_order(order['order_id'], products)

        return order['order_id']

    def process_articles(self, articles):
        products = []
        for article in articles:
            product = self.get_product(article)
            products.append((product, article))

            subassemblies = self.process_subassemblies(article['subassemblies'])

            self.create_bom(product, article['cnt'], subassemblies)

        return products

    def process_subassemblies(self, subassemblies):
        processed_subassemblies = []
        for subassembly in subassemblies:
            subunit = self.get_product(subassembly)
            processed_subassemblies.append((subunit, subassembly))

            parts_and_couplers = self.process_parts_and_connectors(subassembly)

            self.create_bom(subunit, subassembly['cnt'], parts_and_couplers)

        return processed_subassemblies

    def process_parts_and_connectors(self, subassembly):
        parts = [(self.get_product(part), part) for part in subassembly['parts']]
        couplers = [(self.get_product(connector), connector) for connector in subassembly['connectors']]

        return parts + couplers

    def create_bom(self, product, quantity, bom_lines):
        self.env['mrp.bom'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_qty': quantity,
            'bom_line_ids': [(0, 0, {
                'product_id': p.id,
                'product_qty': pdata['cnt'],
            }) for p, pdata in bom_lines],
        })

    def update_sale_order(self, order_id, products):
        sale_order = self.env['sale.order'].search([('name', '=', order_id)])
        # create sale order if it does not exist
        if not sale_order:
            self.env['sale.order'].create({
                'name': order_id,
                'company_id': 1,
                'partner_id': 2})

        # add / replace products in sale order that was updated
        for p, pdata in products:
            existing_line = sale_order.order_line.filtered(lambda x: x.position == pdata['order_pos'])

            if existing_line:
                existing_line.unlink()

            sale_order.write({
                'order_line': [(0, 0, {
                    'position': pdata['order_pos'],
                    'product_id': p.id,
                    'product_uom_qty': pdata['cnt'],
                })]
            })
        sale_order.boml_received = True
        sale_order.boml_last_updated = datetime.now()

    def get_product(self, article):  # article (subassembly), part, connector, ...
        product = self.env['product.product'].search([('checksum', '=', article['info5'])])
        if not product or not article['info5']:
            product = self.env['product.product'].create({
                # 'product_tmpl_id': product_tmpl.id,
                'name': article['name'],
                # 'barcode': article['barcode'] if article['barcode'] else False,
                'checksum': article['info5'],
            })
        return product
