#-- coding: utf-8 --
#Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    #  Information
    'name': "Flyt Transfer Quantity",
    'version': '17.0.0.0.1',
    'category': 'Custom Development',
    'summary': "Receipt stock move line quantity to zero",
    'description': """
Quantity to zero | TaskID: 4004975
==================================================
When confirming the purchase order the quantities on the stock move lines on purchase receipts are defaulted to be zero 
but user set picked true the quantity is set to the demanded quantity.
""",

    # Author
    'author': 'Odoo PS',
    'website': 'https://www.odoo.com/',
    'license': 'LGPL-3',

    # Dependency
    'depends': ['stock', 'purchase'],
    
    # Other
    'installable': True,
}
