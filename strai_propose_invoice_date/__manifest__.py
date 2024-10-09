# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    #  Information
    'name': 'Strai-Propose Invoice Date',
    'version': '17.0.1.0.0',
    'summary': 'Strai-Propose Invoice Date',
    'description': """
        Purpose - This module will set invoice date same as effective date of delivery order. 
        Task ID : 3223396
    """,
    'category': 'Customization',

    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com/',
    'license': 'LGPL-3',

    # Dependency
    'depends': ['strai'],
    'data': [
    ],

    # Other
    'installable': True,
    'application': False,
    'auto_install': False,
}
