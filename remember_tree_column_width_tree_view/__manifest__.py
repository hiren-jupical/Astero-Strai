{
    "name": "Remember Tree Column Width On Tree View",
    'summary': 'Save column width on tree vew and one2Many field when user resize column width.',
    'description': """
        Save column width on tree vew and one2Many field when user resize column width.
    """,
    'author': "Sonny Huynh",
    "category": "Extra Tools",
    'version': '0.1',
    'depends': ['mail', 'base'],
    'data': [
        'security/ir.model.access.csv',
    ],

    "assets": {
        "web.assets_backend": [
            "remember_tree_column_width_tree_view/static/src/**/*",
        ],
    },

    'images': ['static/description/banner.png'],
    'application': False,
    'license': 'OPL-1',
    'price': 45.00,
    'currency': 'EUR',
}
