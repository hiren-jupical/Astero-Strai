{
    'name': 'EDI BIS3 Payment Means Code on Journal Level',
    'version': '17.0.0.0.0',
    'category': 'Custom Development',
    'author': 'Flytconsulting AS',
    'maintainer': 'Flytconsulting AS',
    'website': 'https://www.flytconsulting.no',
    'summary': "Set payment means code for BIS3 on header level",
    'description': "Set payment means code for BIS3 on header level",
    'license': 'LGPL-3',


    'depends': [
        'account_edi_ubl_cii',
    ],

    'data': [
        'views/account_journal_views.xml'
    ],

    'installable': True,
}