# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Sale Line Custom Vendor",
    "summary": "Adds possibility to change vendor pr. line on the sale order",
    "description": "This module adds a button on sale lines that have products with multiple vendor option. The button opens a wizzard where you can change the vendor for the line",
    'version': '17.0.1.0.0',
    "category": "Sales",
    "author": "Strai Kjøkken AS",
    "website": "https://www.strai.no",
    "depends": [
        'sale', 'sale_purchase'
        ],
    "data": [
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/vendor_wizard.xml',
        'views/res_company_views.xml',
        'security/ir.model.access.csv'
    ],
    "license": "LGPL-3"
}
