# -*- coding: utf-8 -*
{
    #  Information
    'name': 'Flyt Kid number validation',
    'version': '17.0.0.0.1',
    'summary': 'Validate KID numbers in supplier invoices, to improve data quality when payments are sent to the bank.',
    'description': """
       Premise: A valid KID number has a checksum of either mod11 or mod10. If the payment_reference field is set, it needs to comply with this for the confirm button to work.

       Borrows from <a href="https://apps.odoo.com/apps/modules/11.0/l10n_no_kid/">l10n_no_kid</a>
     """,
    'category': 'Customization',
    # Author
    'author': 'Flyt Consulting AS',
    'website': 'https://www.flytconsulting.no',
    'license': 'LGPL-3',
    # Dependency
    'depends': ['account'],
    'data': [        
    ],
}
