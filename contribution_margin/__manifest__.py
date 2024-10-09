# -*- coding: utf-8 -*
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Report Contribution Margin',
    'version': '17.0.0.1.5',
    'summary': 'Report Contribution Margin',
    'description': """
       TASK ID - 3141953, 3874748
     """,
    'category': 'Customization',

    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',

    # Dependency
    'depends': ['analytic', 'account', 'strai'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/account_analytic_view.xml',
        'views/contribution_margin_report_views.xml',
        'views/account_analytic_line_views.xml',
    ],

    # Other
    'installable': True,
    'auto_install': False,
    'application': False,
}
