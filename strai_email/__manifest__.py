# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Strai Custom Email Behaviour',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Override certain behavior for outgoing emails',
    'depends': ['mail', 'account', 'strai'],
    'data': [
        "wizard/mail_compose_message_views.xml",
    ],
    'installable': True,
    'application': False,
}
