# -*- coding: utf-8 -*
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    #  Information
    'name': 'Flyt Peppol Dispatch Advice Incoming',
    'version': '17.0.0.1.1',
    'summary': 'Flyt Peppol Dispatch Advice Incoming',
    'description': """
        Task ID -3932770
        Update Json into stock.picking
    """,
    'category': 'Customization',

    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',

    # Dependency
    'depends': ['stock', 'flyt_peppol_id_match'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/res_company_inherit_view.xml'
    ],

    # Other
    'installable': True,
    'auto_install': False,
    'application': False,
}
