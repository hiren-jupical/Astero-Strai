# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    dispatch_tracking_url = fields.Char('Dispatch Tracking Number URL', copy=False)
