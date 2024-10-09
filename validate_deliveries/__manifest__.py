# -*- coding: utf-8 -*
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Validate Deliveries",
    "version": "17.0.1.0.1",
    "license": "LGPL-3",
    "author": "Strai Kjøkken AS",
    "website": "https://www.strai.no",
    "description": "Cron job for fulfilling delivery orders for sale orders marked as delivered via the Strai Trunk",
    "category": "Stock",
    "depends": ['sale', 'purchase', 'strai'],
    "data": [
        'data/ir_cron_data.xml',
    ],
}
