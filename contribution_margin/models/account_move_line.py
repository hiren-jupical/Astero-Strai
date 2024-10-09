# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    move_type = fields.Selection(store=True, related='move_id.move_type')
