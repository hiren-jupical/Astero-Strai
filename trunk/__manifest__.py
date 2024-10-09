# -*- coding: utf-8 -*-
{
    'name': "Trunk",
    'summary': "Communication with Trunk middleware",

    'description': "Communication with Trunk middleware. Creates basic functionalities with GET, POST, etc to Trunk",
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'Uncategorized',
    'version': '17.0.1.0.0',
    'depends': ['base', 'base_setup', 'sales_team'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/trunk_endpoint_views.xml',
        'security/ir.model.access.csv'
    ],
    'license': "LGPL-3"
}
