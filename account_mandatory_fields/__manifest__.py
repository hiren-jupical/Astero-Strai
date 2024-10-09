{
    'name': "Account mandatory fields",
    'summary': """
        Require some fields to be mandatory on spesific accounts""",
    'description': """
        Require some fields to be mandatory on spesific accounts
    """,
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'Accounting',
    'version': '17.0.0.1.1',
    'depends': ['base', 'account', 'invoice_approval_process'],
    'data': [
        'views/account_account_views.xml'
    ],
    'license': 'LGPL-3'
}
