{
    'name': 'Invoice and Bill Approval Process',
    'version': '17.0.1.3.8',
    'summary': """Add approval flow on invoice and vendor bill.""",
    'description': """ This Module will add approval flow on invoice and vendor bill""",
    'author': 'Strai Kjøkken AS',
    'website': "https://www.strai.no",
    'category': 'Accounting',
    'depends': [
        'account', 'documents', 'account_accountant', 'base', 'purchase', 'strai', 'trunk_ocr'
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'security/security.xml',
        'views/res_company_views.xml',
        'data/ir_cron_compute_invoice_approver.xml',
        'data/ir_actions_server_recompute_approver.xml',
    ],
    'license': 'LGPL-3',
}
