from odoo.tests import TransactionCase, tagged
from . import resources


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(self.registry.reset_changes)
        self.addCleanup(self.registry.clear_caches)

        resources.permission_odoobot_allcompanies(self.env)

        # company object
        self.company_production = self.env['res.company'].search([('production', '=', True)])

        self.customer = resources.create_customer(self.env)
        resources.create_suppliers(self.env)  # return values are not used

        self.saleorder_manual_shop = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': 3
        })
        self.saleorder_manual_factory = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company_production.id
        })

        self.saleorder_import_shop = self.env['sale.order'].search([('name', '=', self.env['sale.order'].create_sale_orders(resources.winnerorder_shop)[0])])
        self.saleorder_import_factory = self.env['sale.order'].search([('name', '=', self.env['sale.order'].create_sale_orders(resources.winnerorder_factory)[0])])  # free shop or aftermarket

        resources.create_saleorder_lines(self.saleorder_manual_shop, False)
        resources.create_saleorder_lines(self.saleorder_manual_factory, True)
        resources.create_saleorder_lines(self.saleorder_import_shop, False)
        resources.create_saleorder_lines(self.saleorder_import_factory, True)

    def test_manual_sale_order(self):
        # check if the orders in shop starts with SB
        self.assertEqual(self.saleorder_manual_shop.name[:2], 'SB')
        self.assertEqual(self.saleorder_import_shop.name[:2], 'SB')

    def test_winner_sale_order(self):
        # check if the orders in factory starts with SF
        self.assertEqual(self.saleorder_manual_factory.name[:2], 'SF')
        self.assertEqual(self.saleorder_import_factory.name[:2], 'SF')

    def test_form_sale_order(self):
        pass
