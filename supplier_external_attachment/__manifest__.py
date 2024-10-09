{
    'name': "Supplier External Attachment",
    'summary': """
        Append attachment from external systems to specific suppliers when purchasing""",
    'description': """
        Append attachment from external systems to specific suppliers when purchasing""",
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'Customization',
    'version': '17.0.0.0.1',
    'depends': ['strai', 'trunk'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'license': 'LGPL-3'
}
