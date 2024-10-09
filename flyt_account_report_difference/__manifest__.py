# -*- coding: utf-8 -*
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    #  Information
    'name': 'flyt account report difference',
    'version': '17.0.0.1.0',
    'summary': 'flyt account report difference.',
    'description': """
       New difference column in account reports. 
       Task ID : 4010918
     """,

    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',

    # Dependency
    'depends': ['account_accountant'],
    'data': [
    ],

    # Assets
    'assets': {
        'web.assets_backend': [
            'flyt_account_report_difference/static/src/components/**/*',
        ],
    },

    # Other
    'installable': True,
    'auto_install': False,
    'application': False,
}
