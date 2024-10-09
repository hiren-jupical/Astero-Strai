{
    'name': "Analytic Account selection groups",
    'description': """
       This module makes the selection of analytic accounts easier. When selecting a financial account user is limited to 
       select analytic accounts set up on the financial account. 
    """,
    "author": "Strai Kjøkken AS",
    "website": "https://www.strai.no",
    'license': 'LGPL-3',
    'version': '17.0.1.0.2',
    'depends': [
        'base',
        'account_accountant',
        'account',
        'strai',
        'strai_analytic_account'
    ],
    'data': [
        'views/account_account_views.xml',
        'views/account_move_form_views.xml',
    ],
}
