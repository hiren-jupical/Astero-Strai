import datetime

from odoo.tests import SingleTransactionCase, tagged
from odoo import Command
from . import resources


@tagged('post_install', '-at_install')
class TestPricelist(SingleTransactionCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(self.registry.reset_changes)
        self.addCleanup(self.registry.clear_caches)

        resources.permission_odoobot_allcompanies(self.env)

        # company object
        self.company_production = self.env['res.company'].search([('production', '=', True)])
        self.company_shop = self.env['res.company'].browse(2)

        # suppliers. res.partner object
        self.supplier_factory = self.company_production.partner_id
        self.supplier_fancy, self.supplier_mediocre, self.supplier_cheap = resources.create_suppliers(self.env)

        # brands and series
        self.brand_fancy = self.env['akustikken.product.brand'].create({
            'name': 'fancy',
            'product_series_ids': [
                Command.create({'name': 'fancy'}),
                Command.create({'name': 'stove'}),
                Command.create({'name': 'refrigerator'})]
        })
        self.brand_mediocre = self.env['akustikken.product.brand'].create({
            'name': 'mediocre',
            'product_series_ids': [
                Command.create({'name': 'mediocre'}),
                Command.create({'name': 'freezer'})
            ]
        })
        self.brand_cheap = self.env['akustikken.product.brand'].create({
            'name': 'cheap',
            'product_series_ids': [
                Command.create({'name': 'cheap'})
            ]
        })

        # products
        self.product_fancy_noseries = self.env['product.product'].create({
            'name': 'FancyProductNoSeries',
            'product_brand_id': self.brand_fancy.id,
            'seller_ids': [Command.create({
                'partner_id': self.supplier_fancy.id,
                'company_id': self.company_production.id,
                'product_code': 'FancyProductNoSeries',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'FancyProductNoSeries',
                'price': 0
            })]
        })
        self.product_fancy_fancy = self.env['product.product'].create({
            'name': 'FancyProductFancy',
            'product_brand_id': self.brand_fancy.id,
            'product_series_id': self.brand_fancy.product_series_ids.filtered(lambda x: x.name == 'fancy').id,
            'seller_ids': [Command.create({
                'partner_id': self.supplier_fancy.id,
                'company_id': self.company_production.id,
                'product_code': 'FancyProductFancy',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'FancyProductFancy',
                'price': 0
            })]
        })
        self.product_fancy_stove = self.env['product.product'].create({
            'name': 'FancyProductStove',
            'product_brand_id': self.brand_fancy.id,
            'product_series_id': self.brand_fancy.product_series_ids.filtered(lambda x: x.name == 'stove').id,
            'seller_ids': [Command.create({
                'partner_id': self.supplier_fancy.id,
                'company_id': self.company_production.id,
                'product_code': 'FancyProductStove',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'FancyProductStove',
                'price': 0
            })]
        })
        self.product_fancy_refrigerator = self.env['product.product'].create({
            'name': 'FancyProductRefrigerator',
            'product_brand_id': self.brand_fancy.id,
            'product_series_id': self.brand_fancy.product_series_ids.filtered(lambda x: x.name == 'refrigerator').id,
            'seller_ids': [Command.create({
                'partner_id': self.supplier_fancy.id,
                'company_id': self.company_production.id,
                'product_code': 'FancyProductRefrigerator',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'FancyProductRefrigerator',
                'price': 0
            })]
        })
        self.product_mediocre_noseries = self.env['product.product'].create({
            'name': 'MediocreProductNoSeries',
            'product_brand_id': self.brand_mediocre.id,
            'seller_ids': [Command.create({
                'partner_id': self.supplier_mediocre.id,
                'company_id': self.company_production.id,
                'product_code': 'MediocreProductNoSeries',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'MediocreProductNoSeries',
                'price': 0
            })]
        })
        self.product_mediocre_mediocre = self.env['product.product'].create({
            'name': 'MediocreProductMediocre',
            'product_brand_id': self.brand_mediocre.id,
            'product_series_id': self.brand_mediocre.product_series_ids.filtered(lambda x: x.name == 'mediocre'),
            'seller_ids': [Command.create({
                'partner_id': self.supplier_mediocre.id,
                'company_id': self.company_production.id,
                'product_code': 'MediocreProductMediocre',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'MediocreProductMediocre',
                'price': 0
            })]
        })
        self.product_mediocre_freezer = self.env['product.product'].create({
            'name': 'MediocreProductFreezer',
            'product_brand_id': self.brand_mediocre.id,
            'product_series_id': self.brand_mediocre.product_series_ids.filtered(lambda x: x.name == 'freezer'),
            'seller_ids': [Command.create({
                'partner_id': self.supplier_mediocre.id,
                'company_id': self.company_production.id,
                'product_code': 'MediocreProductFreezer',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'MediocreProductFreezer',
                'price': 0
            })]
        })
        self.product_cheap_noseries = self.env['product.product'].create({
            'name': 'CheapProductNoSeries',
            'product_brand_id': self.brand_cheap.id,
            'seller_ids': [Command.create({
                'partner_id': self.supplier_cheap.id,
                'company_id': self.company_production.id,
                'product_code': 'CheapProductNoSeries',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'CheapProductNoSeries',
                'price': 0
            })]
        })
        self.product_cheap_cheap = self.env['product.product'].create({
            'name': 'CheapProductCheap',
            'product_brand_id': self.brand_cheap.id,
            'product_series_id': self.brand_cheap.filtered(lambda x: x.name == 'cheap'),
            'seller_ids': [Command.create({
                'partner_id': self.supplier_cheap.id,
                'company_id': self.company_production.id,
                'product_code': 'CheapProductCheap',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'CheapProductCheap',
                'price': 0
            })]
        })
        self.product_nobrand = self.env['product.product'].create({
            'name': 'Nobrand',
            'seller_ids': [Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_production.id,
                'product_code': 'Nobrand',
                'price': 500.0
            }), Command.create({
                'partner_id': self.supplier_factory.id,
                'company_id': self.company_shop.id,
                'product_code': 'Nobrand',
                'price': 0
            })]
        })

        # pricelists
        # public. Used as reference in many other pricelists
        self.pricelist_public = self.env['product.pricelist'].browse(1)  # public pricelist is id 1

        # purchase factory
        self.pricelist_purchase_std = self.env['product.pricelist'].create({
            'name': 'TEST Std purchase',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': False,
            'item_ids': [
                # general rule - if no other rules match, calculate extreme discount to not approve anything automatically
                Command.create({
                    'compute_price': 'formula',
                    'base': 'pricelist',
                    'base_pricelist_id': self.pricelist_public.id,
                    'applied_on': '3_global',
                    'price_discount': 99.0,
                    'company_id': self.company_production.id
                }),
                # if no brand, and product specific price, apply discount to sale price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'applied_on': '0_product_variant',
                    'product_id': self.product_nobrand.id,
                    'price_discount': 70.0,
                    'company_id': self.company_production.id
                }),
                # brand, but no series, apply discount to sale price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'applied_on': '4_brands',
                    'brand_id': self.brand_fancy.id,
                    'price_discount': 68.0,
                    'company_id': self.company_production.id
                }),
                # brand and series, apply discount to sale price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'applied_on': '5_series',
                    'brand_id': self.brand_fancy.id,
                    'series_id': self.brand_fancy.product_series_ids.filtered(lambda x: x.name == 'fancy').id,
                    'price_discount': 65.0,
                    'company_id': self.company_production.id
                }),
                # brand purchase price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'purchase_price',
                    'applied_on': '4_brands',
                    'brand_id': self.brand_mediocre.id,
                    'company_id': self.company_production.id
                }),
                # brand series purchase price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'purchase_price',
                    'applied_on': '5_series',
                    'brand_id': self.brand_mediocre.id,
                    'series_id': self.brand_mediocre.product_series_ids.filtered(lambda x: x.name == 'mediocre').id,
                    'company_id': self.company_production.id
                }),
                # product variant purchase price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'purchase_price',
                    'applied_on': '0_product_variant',
                    'product_id': self.product_mediocre_noseries.id,
                    'company_id': self.company_production.id
                })
            ]
        })
        # create pricelist for every scenario to cover that correct pricelist is selected. Calculations only happens on one pricelist to avoid unnecessary tests
        self.pricelist_purchase_exh = self.env['product.pricelist'].create({
            'name': 'TEST exh purchase',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': False
        })
        self.pricelist_purchase_builder = self.env['product.pricelist'].create({
            'name': 'TEST builder purchase',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': False
        })
        self.pricelist_purchase_project = self.env['product.pricelist'].create({
            'name': 'TEST project purchase',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': False
        })
        self.pricelist_purchase_campaign = self.env['product.pricelist'].create({
            'name': 'TEST campaign purchase',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': False
        })

        # intercompany
        self.pricelist_ic_std = self.env['product.pricelist'].create({
            'name': 'TEST std ic',
            'company_id': self.company_production.id,
            'order_type': 'standard',
            'purchase_pricelist_id': self.pricelist_purchase_std.id,
            'item_ids': [
                # general rule - if no other rules match, calculate 0 discount to not generate discount to shop
                Command.create({
                    'compute_price': 'formula',
                    'base': 'pricelist',
                    'base_pricelist_id': self.pricelist_public.id,
                    'applied_on': '3_global',
                    'price_discount': 0.0,
                    'company_id': self.company_production.id
                }),
                # if no brand, and product specific price, apply discount to sale price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'applied_on': '0_product_variant',
                    'product_id': self.product_nobrand.id,
                    'price_discount': 50.0,
                    'company_id': self.company_production.id
                }),
                # brand, but no series, apply discount to sale price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'applied_on': '4_brands',
                    'brand_id': self.brand_fancy.id,
                    'price_discount': 47.0,
                    'company_id': self.company_production.id
                }),
                # brand and series, apply discount to sale price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'applied_on': '5_series',
                    'brand_id': self.brand_fancy.id,
                    'series_id': self.brand_fancy.product_series_ids.filtered(lambda x: x.name == 'fancy').id,
                    'price_discount': 43.0,
                    'company_id': self.company_production.id
                }),
                # brand purchase price, negative discount
                Command.create({
                    'compute_price': 'formula',
                    'base': 'purchase_price',
                    'applied_on': '4_brands',
                    'brand_id': self.brand_mediocre.id,
                    'company_id': self.company_production.id,
                    'price_discount': -11.7
                }),
                # brand series purchase price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'purchase_price',
                    'applied_on': '5_series',
                    'brand_id': self.brand_mediocre.id,
                    'series_id': self.brand_mediocre.product_series_ids.filtered(lambda x: x.name == 'mediocre').id,
                    'company_id': self.company_production.id,
                    'price_discount': -8.0
                }),
                # product variant purchase price
                Command.create({
                    'compute_price': 'formula',
                    'base': 'purchase_price',
                    'applied_on': '0_product_variant',
                    'product_id': self.product_cheap_noseries.id,
                    'company_id': self.company_production.id,
                    'price_discount': -5.0
                })
            ]
        })
        # test based on different pricelist in multiple hierarchies (based on-pricelists)
        self.pricelist_ic_exh = self.env['product.pricelist'].create({
            'name': 'TEST exh ic',
            'company_id': self.company_production.id,
            'order_type': 'exhibit',
            'purchase_pricelist_id': self.pricelist_purchase_exh.id,
            'item_ids': [
                # general rule - if no other rules match, calculate same discount as the dependent pricelist
                Command.create({
                    'compute_price': 'formula',
                    'base': 'pricelist',
                    'base_pricelist_id': self.pricelist_ic_std.id,
                    'applied_on': '3_global',
                    'price_discount': 0.0,
                    'company_id': self.company_production.id
                }),
                # brand, extra discount (on top on inherited discount - 42 % + 10 % = 47,8 %
                Command.create({
                    'compute_price': 'formula',
                    'base': 'pricelist',
                    'base_pricelist_id': self.pricelist_ic_std.id,
                    'applied_on': '4_brands',
                    'brand_id': self.brand_fancy.id,
                    'price_discount': 10.0,
                    'company_id': self.company_production.id
                })
            ]
        })
        # create pricelist for every scenario to cover that correct pricelist is selected. Calculations only happens on one pricelist to avoid unnecessary tests
        self.pricelist_ic_builder3035 = self.env['product.pricelist'].create({
            'name': 'TEST builder 3035 ic',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': self.pricelist_purchase_builder.id
        })
        self.pricelist_ic_builder3842 = self.env['product.pricelist'].create({
            'name': 'TEST builder 3842 ic',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': self.pricelist_purchase_project.id
        })
        self.pricelist_ic_project = self.env['product.pricelist'].create({
            'name': 'TEST project ic',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': self.pricelist_purchase_project.id
        })
        self.pricelist_ic_campaign = self.env['product.pricelist'].create({
            'name': 'TEST campaign ic',
            'company_id': self.company_production.id,
            'order_type': 'purchase',
            'purchase_pricelist_id': self.pricelist_purchase_campaign.id
        })

        # shop
        self.pricelist_builder35 = self.env['product.pricelist'].create({
            'name': 'TEST Proff 35',
            'company_id': False,
            'order_type': False,
            'purchase_pricelist_id': False,
            'item_ids': [
                Command.create({
                    'compute_price': 'formula',
                    'base': 'pricelist',
                    'base_pricelist_id': self.pricelist_public.id,
                    'applied_on': '3_global'
                })
            ]
        })
        self.pricelist_builder42 = self.env['product.pricelist'].create({
            'name': 'TEST Proff 42',
            'company_id': False,
            'order_type': False,
            'purchase_pricelist_id': False,
            'item_ids': [
                Command.create({
                    'compute_price': 'formula',
                    'base': 'pricelist',
                    'base_pricelist_id': self.pricelist_public.id,
                    'applied_on': '3_global'
                })
            ]
        })

        # campaigns
        self.campaign_global = self.env['strai.campaign'].create({
            'name': 'Global campaign',
            'campaign_company_ids': self.env['res.company'].search([]).ids,
            'campaign_pricelist_id': self.pricelist_ic_campaign.id,
            'campaign_info': 'campinfo',
            'from_date': datetime.datetime(2023, 1, 1),
            'to_date': datetime.datetime(2023, 3, 31)
        })

        # builders
        self.builder_35 = self.env['res.partner'].create(
            {'name': 'Builder35', 'is_builder': True, 'internal_pricelist_id': self.pricelist_ic_builder3035.id})
        self.builder_42 = self.env['res.partner'].create(
            {'name': 'Builder42', 'is_builder': True, 'internal_pricelist_id': self.pricelist_ic_builder3842.id})

        # projects and apartments
        self.project_11_apartments = self.env['sales.projects'].create({
            'name': 'TestProject11Apartments',
            'developer_id': self.builder_42.id
        })
        self.project_11_apartment_1 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-1', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_2 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-2', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_3 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-3', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_4 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-4', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_5 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-5', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_6 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-6', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_7 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-7', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_8 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-8', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_9 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-9', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_10 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-10', 'sales_project_id': self.project_11_apartments.id})
        self.project_11_apartment_11 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment11-11', 'sales_project_id': self.project_11_apartments.id})

        self.project_9_apartments = self.env['sales.projects'].create({
            'name': 'TestProject9Apartments',
            'developer_id': self.builder_42.id
        })
        self.project_9_apartment_1 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-1', 'sales_project_id': self.project_9_apartments.id})
        self.project_9_apartment_2 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-2', 'sales_project_id': self.project_9_apartments.id})
        self.project_9_apartment_3 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-3', 'sales_project_id': self.project_9_apartments.id})
        self.project_9_apartment_4 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-4', 'sales_project_id': self.project_9_apartments.id})
        self.project_9_apartment_5 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-5', 'sales_project_id': self.project_9_apartments.id})
        self.project_9_apartment_6 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-6', 'sales_project_id': self.project_9_apartments.id})
        self.project_9_apartment_7 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-7', 'sales_project_id': self.project_9_apartments.id})
        self.project_9_apartment_8 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-8', 'sales_project_id': self.project_9_apartments.id})
        self.project_9_apartment_9 = self.env['sales.projects.apartment'].create(
            {'name': 'TestApartment9-9', 'sales_project_id': self.project_9_apartments.id})

        # customer
        self.customer = self.env['res.partner'].create({'name': 'Good Customer'})

        # sale orders
        self.saleorder_manual_shop = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': 2
        })
        self.saleorder_manual_factory = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company_production.id
        })
        self.saleorder_import_shop = self.env['sale.order'].search([('name', '=', self.env['sale.order'].create_sale_orders(resources.winnerorder_shop)[0])])
        self.saleorder_import_factory = self.env['sale.order'].search([('name', '=', self.env['sale.order'].create_sale_orders(resources.winnerorder_factory)[0])])  # free shop or aftermarket

        # setup default values in sale orders to allow us to confirm them. Some fields may vary between tests, but is loaded with defaults at first
        resources.write_saleorder_defaults(self.saleorder_manual_shop)
        resources.write_saleorder_defaults(self.saleorder_manual_factory)
        resources.write_saleorder_defaults(self.saleorder_import_shop)
        resources.write_saleorder_defaults(self.saleorder_import_factory)

        # create/append some default sale order lines
        resources.create_saleorder_lines(self.saleorder_manual_shop, False)
        resources.create_saleorder_lines(self.saleorder_manual_factory, True)
        resources.create_saleorder_lines(self.saleorder_import_shop, False)
        resources.create_saleorder_lines(self.saleorder_import_factory, True)

    # correct calculation in correct places
    def test_shop_saleorder_use_sale_price(self):
        # no calculation, should use prices coming from kitchen drawing software
        # might change when price calculation module is ready in Odoo

        # assert public pricelist selected
        self.assertEqual(self.saleorder_manual_shop.pricelist_id.id, self.pricelist_public.id)
        self.assertEqual(self.saleorder_import_shop.pricelist_id.id, self.pricelist_public.id)

        # assert no discount calculated orders
        self.assertEqual(len(self.saleorder_manual_shop.order_line.filtered(lambda x: x.discount != 0)), 0)
        # assert Winner discount on the imported order
        self.assertEqual(len(self.saleorder_import_shop.order_line.filtered(lambda x: x.discount != 0)), 0)

        # assert sale price from entered price, not on product card
        self.assertEqual(len(self.saleorder_manual_shop.order_line.filtered(lambda x: x.price_unit > 100)), 10)

    def test_shop_purchaseorder_use_intercompany_price(self):
        self.saleorder_manual_shop._action_confirm()
        self.assertEqual(self.saleorder_manual_shop.state, 'sale')

        self.assertEqual(self.saleorder_manual_shop.purchase_order_count, 1)
        po = self.saleorder_manual_shop.auto_purchase_order_id[0]
        # assert discount gathered from intercompany pricelist with order type standard
        # discount from sale price, based on brand
        self.assertEqual(po.order_line[0].discount, 47.0)
        self.assertEqual(po.order_line[0].price_unit, 1000.0)
        # discount from sale price, based on brand and series
        self.assertEqual(po.order_line[1].discount, 43.0)
        self.assertEqual(po.order_line[1].price_unit, 1000.0)
        self.assertEqual(po.order_line[2].discount, 43.0)
        self.assertEqual(po.order_line[2].price_unit, 1000.0)
        self.assertEqual(po.order_line[3].discount, 43.0)
        self.assertEqual(po.order_line[3].price_unit, 1000.0)
        # surcharge on purchase price in production company should equal purchase price in shop, brand
        self.assertEqual(po.order_line[4].discount, (800.0 - 500.0 * 1.117) / 800)
        self.assertEqual(po.order_line[4].price_unit, 800.0)
        # surcharge on purchase price in production company should equal purchase price in shop, brand and series
        self.assertEqual(po.order_line[5].discount, (800.0 - 500.0 * 1.08) / 800)
        self.assertEqual(po.order_line[5].price_unit, 800.0)
        # surcharge purchase price product variant
        self.assertEqual(po.order_line[7].discount, (700.0 - 500.0 * 1.05) / 700)
        self.assertEqual(po.order_line[7].price_unit, 700)

        # TODO check subtotal, total and taxes
        # TODO check order total
        # standard Odoo does not compute discount on purchase orders

    def test_factory_saleorder_use_pricelist(self):
        shop_po = self.saleorder_manual_shop.auto_purchase_order_id[0]
        shop_po.button_confirm()
        sf = self.env['sale.order'].search([('name', '=', shop_po.client_order_ref)])
        self.assertEqual(len(sf), 1)
        self.assertEqual(sf.state, 'draft')
        self.assertEqual(sf.pricelist_id.id, self.pricelist_ic_std.id)

        # assert discount gathered from intercompany pricelist with order type standard
        # discount from sale price, based on brand
        self.assertEqual(sf.order_line[0].discount, 47.0)
        self.assertEqual(sf.order_line[0].price_unit, 1000.0)
        # discount from sale price, based on brand and series
        self.assertEqual(sf.order_line[1].discount, 43.0)
        self.assertEqual(sf.order_line[1].price_unit, 1000.0)
        self.assertEqual(sf.order_line[2].discount, 43.0)
        self.assertEqual(sf.order_line[2].price_unit, 1000.0)
        self.assertEqual(sf.order_line[3].discount, 43.0)
        self.assertEqual(sf.order_line[3].price_unit, 1000.0)
        # surcharge on purchase price in production company should equal purchase price in shop, brand
        self.assertEqual(sf.order_line[4].discount, (800.0 - 500.0 * 1.117) / 800)
        self.assertEqual(sf.order_line[4].price_unit, 800.0)
        # surcharge on purchase price in production company should equal purchase price in shop, brand and series
        self.assertEqual(sf.order_line[5].discount, (800.0 - 500.0 * 1.08) / 800)
        self.assertEqual(sf.order_line[5].price_unit, 800.0)
        # surcharge purchase price product variant
        self.assertEqual(sf.order_line[7].discount, (700.0 - 500.0 * 1.05) / 700)
        self.assertEqual(sf.order_line[7].price_unit, 700)

    # TODO check factory purchase prices

    # choose correct pricelist
    # def test_ordertype_campaign(self):
    #     pass
    #
    # def test_ordertype_project(self):
    #     pass
    #
    # def test_ordertype_builder(self):
    #     pass
