from odoo.tests.common import TransactionCase


class TestSaleOrderBomlUpdate(TransactionCase):

    def setUp(self):
        super(TestSaleOrderBomlUpdate, self).setUp()
        # Create necessary records for testing
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner'
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'checksum': 'AAA'
        })

    def test_update_sale_order_create_new(self):
        """Test creating a new sale order with given products."""
        order_id = 'SO123'
        products = [(self.product, {'order_pos': 1, 'cnt': 5})]

        self.env['sale.order'].update_sale_order(order_id, products)

        sale_order = self.env['sale.order'].search([('name', '=', order_id)])
        self.assertTrue(sale_order, "Sale order should be created.")
        self.assertEqual(len(sale_order.order_line), 1, "There should be one order line.")
        self.assertEqual(sale_order.order_line.position, 1, "Order line position should match.")
        self.assertEqual(sale_order.order_line.product_uom_qty, 5, "Product quantity should match.")

    def test_update_sale_order_replace_line(self):
        """Test replacing an existing sale order line with the same position."""
        order_id = 'SO123'
        products_initial = [(self.product, {'order_pos': 1, 'cnt': 5})]
        products_updated = [(self.product, {'order_pos': 1, 'cnt': 10})]

        # Create initial sale order with one product
        self.env['sale.order'].update_sale_order(order_id, products_initial)

        sale_order = self.env['sale.order'].search([('name', '=', order_id)])
        self.assertEqual(sale_order.order_line.product_uom_qty, 5, "Initial quantity should be 5.")

        # Update the same sale order with new quantity for the same position
        self.env['sale.order'].update_sale_order(order_id, products_updated)

        sale_order = self.env['sale.order'].search([('name', '=', order_id)])
        self.assertEqual(len(sale_order.order_line), 1, "There should still be only one order line.")
        self.assertEqual(sale_order.order_line.product_uom_qty, 10, "Updated quantity should be 10.")

    def test_update_sale_order_add_new_line(self):
        """Test adding a new line to an existing sale order."""
        order_id = 'SO123'
        product2 = self.env['product.product'].create({
            'name': 'Test Product 2',
            'list_price': 50.0,
        })
        products_initial = [(self.product, {'order_pos': 1, 'cnt': 5})]
        products_new_line = [(product2, {'order_pos': 2, 'cnt': 3})]

        # Create initial sale order with one product
        self.env['sale.order'].update_sale_order(order_id, products_initial)

        sale_order = self.env['sale.order'].search([('name', '=', order_id)])
        self.assertEqual(len(sale_order.order_line), 1, "Initial order should have one line.")

        # Add new line with different position
        self.env['sale.order'].update_sale_order(order_id, products_new_line)

        sale_order = self.env['sale.order'].search([('name', '=', order_id)])
        self.assertEqual(len(sale_order.order_line), 2, "There should be two order lines.")
        self.assertEqual(sale_order.order_line.filtered(lambda l: l.position == 2).product_uom_qty, 3, "New line should have correct quantity.")
