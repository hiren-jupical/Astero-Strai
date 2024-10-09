#  -*- coding: utf-8 -*-
#  Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class DispatchAdviceStatus(models.Model):
    _name = 'dispatch.advice.status'
    _description = "Dispatch Advice Status"

    picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True, required=True)
    dispatch_note = fields.Html(string="Dispatch Table", readonly=True)
    shipment_number = fields.Char('Shipment Number', copy=False, readonly=True)
    tracking_number = fields.Char('Tracking Number', copy=False, readonly=True)
    tracking_number_link = fields.Char(string="Tracking Number URL", compute ="_compute_tracking_number_link")
    delivery_date = fields.Date('Delivery Date', copy=False, readonly=True)
    shipment_gross_weight = fields.Char('Shipment Gross Weight', copy=False, readonly=True)
    shipment_gross_volume = fields.Char('Shipment Gross Volume', copy=False, readonly=True)
    status = fields.Selection([
        ('exceptions', 'Received with exceptions'),
        ('received', 'Received')
    ], string='Status', copy=False, readonly=True)

    def _compute_tracking_number_link(self):
        for rec in self:
            rec.tracking_number_link = (rec.picking_id.company_id.dispatch_tracking_url\
                or ' ') + rec.tracking_number
