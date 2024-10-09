{
    'name': "Auto invoice approval",
    'summary': """ Automatically approve invoices that match all required criteria """,
    'description': """ Automatically approve invoiced that match all required criteria """,
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    'category': 'Accounting',
    'version': '17.0.0.0.1',
    'depends': ['account', 'strai', 'trunk_ocr', 'invoice_approval_process'],
    'data': [
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'data/ir_cron_auto_invoice_approval.xml',
    ],
    'license': 'LGPL-3'
}
