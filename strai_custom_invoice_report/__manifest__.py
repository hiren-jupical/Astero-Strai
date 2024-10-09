# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Invoice Report Customisation',
    'version': '17.0.0.1.0',
    'author': 'Odoo PS',
    'category': 'custom',
    'website': 'https://www.odoo.com/',
    'summary': 'Invoice Report Customisation',
    'description': """
        Invoice Report Customisation
        Task ID 2957042 | Version 16.0 EE
    """,
    'license': 'LGPL-3',
    'depends': [
        'sale_stock', 'strai', 'account_followup'
    ],
    'data': [
        'report/custom_invoice_report_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
}
