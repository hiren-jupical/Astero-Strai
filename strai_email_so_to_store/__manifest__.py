# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    # Information
    'name': 'Strai Email So To Store',
    'version': '17.0.0.0.1',
    'summary': ' Strai Email So To Store',
    'description': """ 
        Strai Email So To Store
        Add field into partner category -> f_store_email_recipient_domain for filter partner record according
        to f_store_email_recipient_domain field when click into sale -> Epost til butikk(button).
        TaskId - 3337890, 3582129
    """,
    'category': 'Customization',

    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com/',
    'license': 'LGPL-3',

    # Dependency
    'depends': ['sale_management', 'strai'],
    'data': [
        'data/mail_template_data.xml',
        'views/sale_order_view.xml',
        'views/res_partner_category_view.xml',
        'wizard/mail_compose_message_view.xml'
    ],

    # Other
    'installable': True,
    'auto_install': False,
}
