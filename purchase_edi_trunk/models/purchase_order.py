from datetime import datetime
import requests
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    edi_status = fields.Selection([
        ('new', 'New'),
        ('processed', 'Processed'),
        ('failed', 'Failed')
    ], required=False, readonly=False, store=True, compute='onchange_partner_id_purchase_edi')
    edi_sent_timestamp = fields.Datetime()
    edi_color = fields.Many2one('purchase.edi.color', domain="[('partner_id', '=', partner_id)]", required=False)

    @api.onchange('partner_id')
    @api.depends('partner_id')
    def onchange_partner_id_purchase_edi(self):
        for po in self:
            if po.partner_id and po.partner_id.purchase_edi and not po.edi_status:
                po.edi_status = 'new'
            elif po.partner_id and not po.partner_id.purchase_edi:
                po.edi_status = False
            # else - leave status as is

    # on confirm, calculate if it should be sent with EDI, and set EDI status accordingly
    def button_confirm(self):
        for po in self:
            if po.partner_id and po.partner_id.purchase_edi and not po.edi_status:
                po.edi_status = 'new'
        return super(PurchaseOrder, self).button_confirm()

    def send_edi_trunk(self):
        for po in self:
            payload = {
                'reference': po.name,
                'comment': po.info_supplier,
                'purchase_responsible_name': po.user_id.name,
                'purchase_responsible_email': po.user_id.login,
                'delivery_date': po.date_planned.strftime('%Y-%m-%d'),
                'external_sales_order_no': po.external_sales_order_no or False,
                'order_lines': [
                    {
                        'position': line.position,
                        'default_code': line.product_id.default_code,
                        'name': line.product_id.name,
                        'product_color_code': po.edi_color.itemcode or False,
                        'product_color_name': po.edi_color.color or False,
                        'product_code': line.product_id.seller_ids[0].product_code or False,
                        'product_name': line.name or False,
                        'quantity': line.product_uom_qty,
                        'comment': line.edi_comment
                    }
                    for line in po.order_line
                ]
            }

            payload = json.dumps(payload)

            po.edi_sent_timestamp = datetime.now()
            response = requests.request("POST", self._get_base_endpoint() + f'/PurchaseOrder/{po.partner_id.purchase_edi_endpoint}',
                                        headers=self._get_default_headers(),
                                        data=payload)
            if response and response.status_code == 200:
                po.edi_status = 'processed'
            else:
                po.edi_status = 'failed'
                raise UserError(_('ERROR: not able to send purchase to Trunk'))

    # trunk communication
    def _get_base_endpoint(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        operation_mode_id = ir_config_parameter.get_param('strai.trunk_mode')
        trunk_endpoint = self.env['trunk.endpoint'].search([('id', '=', operation_mode_id)])
        return trunk_endpoint.endpoint

    def _get_default_headers(self):
        ir_config_parameter = self.env['ir.config_parameter'].sudo()
        headers = {
            'ApiKey': ir_config_parameter.get_param('strai.trunk_password'),
            'ApiClient': ir_config_parameter.get_param('strai.trunk_username'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return headers
