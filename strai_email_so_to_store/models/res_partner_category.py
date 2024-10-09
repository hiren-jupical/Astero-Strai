# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    f_store_email_recipient_domain = fields.Boolean('Email Recipient Domain', copy=False)
