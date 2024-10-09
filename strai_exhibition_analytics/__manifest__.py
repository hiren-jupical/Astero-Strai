{
    'name': "Strai Exhibition Analytics",
    'summary': """Connects an analytics account when selling exhibitions""",
    'description': """""",
    "author": "Strai Kjøkken AS",
    "website": "https://www.strai.no",
    'category': 'Accounting',
    'version': '17.0.1.0.4',
    'license': 'LGPL-3',
    'depends': ['sale', 'account', 'strai', 'purchase_stock', 'sale_purchase_inter_company_rules'],
    'data': [
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'wizard/analytic_exhibition_lines_views.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
}
