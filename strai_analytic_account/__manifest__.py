{
    'name': "Strai Analytic Account",
    'summary': """
        Make it easy to search and select analytic account on invoices and credit notes""",
    'description': """
        Make it easy to search and select analytic account on invoices and credit notes
    """,
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'Accounting',
    'version': '17.0.1.0.5',
    'depends': ['base', 'account', 'strai'],
    'data': [
        'views/account_move_views.xml',
        'views/account_asset.xml',
    ],
    'license': 'LGPL-3'
}
