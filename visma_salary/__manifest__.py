# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Visma Salary",
    'summary': "Visma Salary integration",
    'description': "Integration to Visma Salary",
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'hr',
    'version': '17.0.2.0.4',
    'depends': ['hr', 'account', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/strai_visma_import_views.xml',
        'wizard/strai_visma_import_link_views.xml',
        'views/res_config_settings_views.xml',
        'data/ir_cron.xml'
    ],
    'license': "LGPL-3"
}
