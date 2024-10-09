{
    'name': "Purchase EDI Trunk",
    'summary': """ Purchase with EDI through Trunk """,
    'description': """
        Purchase with EDI through Trunk
        Add necessary fields to suppliers and purchase orders
        Send correct data to Trunk which will generate and send EDI file
    """,
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'Customization',
    'version': '17.0.1.0.2',
    'depends': ['strai', 'trunk'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml'
    ],
    'license': 'LGPL-3'
}
