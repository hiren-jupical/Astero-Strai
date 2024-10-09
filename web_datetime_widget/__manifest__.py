{
    'name': 'Custom Datetime Widget',
    'version': '1.0.0',
    'category': 'Cistomization',
    'summary': 'Make date widget work with datetime field',
    'description': "",
    'license': 'LGPL-3',
    'author': 'Odoo PS',
    'depends': [
        'web'
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

    'assets': {
        'web.assets_backend': [
            'web_datetime_widget/static/src/*',
        ],
    },
}
