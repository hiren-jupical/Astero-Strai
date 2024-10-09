# -*- coding: utf-8 -*-
{
    'name': "Trunk Queue",
    'summary': """Queue system to alert Trunk about important changes""",
    'description': """Queue system to alert Trunk about important changes""",
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'Uncategorized',
    'version': '17.0.0.1.0',
    'depends': ['trunk'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_queue.xml',
        'views/trunk_queue_views.xml'
    ],
    'license': "LGPL-3"
}
