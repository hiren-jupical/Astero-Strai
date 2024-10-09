{
    "name": "Order line descriptions on delivery",
    "summary": "Adds order line descriptions (name) to delivery slip",
    "description": "",
    'version': '17.0.1.0.0',
    "category": "Stock",
    "author": "Strai Kjøkken AS",
    "website": "https://www.strai.no",
    "depends": [
        'sale',
        'stock',
        'sale_stock'
    ],
    "data": [
        'report/report_deliveryslip.xml',
        'views/stock_picking_views.xml'
    ],
    "license": "LGPL-3"
}
