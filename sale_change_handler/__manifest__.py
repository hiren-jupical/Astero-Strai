{
    'name': "Sale order change handler",
    'summary': """
        Handle changes to sale orders correctly """,
    'description': """
        Handle changes to sale orders correctly, and handle purchase orders according to the changes
    """,
    'author': "Strai Kjøkken AS",
    'website': "https://www.strai.no",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customization',
    'version': '17.0.1.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'strai', 'sale', 'purchase', 'stock', 'validate_deliveries', 'sale_line_custom_vendor'],  # validate deliveries have overridden the standard _set_quantities_to_reservation in stock.move
    # always loaded
    'data': [
        'views/res_partner_views.xml'
    ],
    'license': "LGPL-3"
}
