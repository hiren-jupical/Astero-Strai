# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Flyt Sales order Gross Total',
    'description': "Flyt Sales order Gross Total",
    'category': 'Sales',
    'author': "OdooIN",
    'depends': [
        'sale_management',
        'account',
        'strai'
    ],

    'version': '17.0.0.3.0',
    'website': "http://www.odoo.com",
    'assets': {
        'web.assets_backend': [
            'flyt_sales_order_gross_total/static/src/components/**/*',
        ],
    },
    'installable': True,
    'license': "LGPL-3"
}
