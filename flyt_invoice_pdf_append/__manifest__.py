# -*- coding: utf-8 -*
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    #  Information
    'name': 'flyt invoice pdf append',
    'version': '17.0.0.1.0',
    'summary': 'Appending PDFs at customer invoice/credit note',
    'description': """
       flyt invoice pdf append Task ID -3277373
     """,
    'category': 'Customization',

    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',

    # Dependency
    'depends': ['account'],
    'data': [
        'views/account_move_view.xml',
    ],

    # Other
    'installable': True,
    'auto_install': False,
    'application': False,
}
