# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    edi_send_purchase_order_confirmation = fields.Boolean(string="Peppol Order Client",
        help="Send Order confirmation file to Peppol EDI")
