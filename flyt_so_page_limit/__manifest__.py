# -*- coding: utf-8 -*
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    #  Information
    'name': 'Flyt SO Page Limit',
    'version': '17.0.0.1.0',
    'summary': 'Increase the number of entries per page for certain SO views',
    'description': """
       Flyt SO Page Limit Task ID -3672442
     """,
    'category': 'Customization',
    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',
    # Dependency
    'depends': ['sale_management'],
    'data': [
        'views/sale_view.xml',
    ],
}
