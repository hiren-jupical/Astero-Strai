# -*- coding: utf-8 -*
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    #  Information
    'name': 'Flyt Peppol Order',
    'version': '17.0.0.1.0',
    'summary': 'Flyt Peppol Order',
    'description': """
        Task ID -3761692
        Creating Xml File in Purchase Order for send into numis accounting network
        Task ID -3908512
        Update data in Purchase Order from Xml file
    """,
    'category': 'Customization',

    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',

    # Dependency
    'depends': ['account_edi', 'stock_dropshipping', 'l10n_no', 'flyt_peppol_id_match'],
    'data': [
        'views/purchase_views.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml'
    ],

    # Other
    'installable': True,
    'auto_install': False,
    'application': False,
}
