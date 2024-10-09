{
    'name': 'Trunk OCR',
    "summary": "This module allow to send vendor bill pdf to trunk software and read the KID no, bank account and PO numbers",
    "description": "This module allow to send vendor bill pdf to trunk software and read the KID no, bank account and PO numbers",
    'category': 'Tools',
    'version': '17.0.0.0.1',
    'license': 'LGPL-3',
    "author": "Strai Kjøkken AS",
    "website": "https://www.strai.no",
    'data': [
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'data/ir_cron_trunk_ocr.xml',
    ],
    'depends': ['trunk', 'account', 'account_accountant', 'strai', 'account_invoice_extract'],
}
