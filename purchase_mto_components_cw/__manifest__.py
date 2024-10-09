{
    'name': "Purchase MTO components CW",
    'summary': """
        Purchase MTO components from CW. Module can be deleted after GO-live with imos""",
    'description': """
        Purchase MTO components from CW. Module can be deleted after GO-live with imos""",
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'Customization',
    'version': '17.0.1.0.0',
    'depends': ['strai', 'trunk'],
    'data': [
        'views/sale_order_views.xml',
        'data/ir_cron_update_mto_stock.xml',
        'data/ir_cron_validate_stock_picking.xml',
    ],
    'license': 'LGPL-3'
}