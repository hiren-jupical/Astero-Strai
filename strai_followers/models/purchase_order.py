# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        return super(PurchaseOrder, self.with_context(from_add_followers=False, mark_rfq_as_sent=True)).button_confirm()

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        company_id = self.env['res.company'].search([('production', '=', True)], limit=1)
        if self.env.context.get('mark_rfq_as_sent', False) \
            and not self.env.context.get('from_add_followers', False) \
            and self.is_production and self.company_id == company_id:
            return True
        return super()._message_subscribe(partner_ids, subtype_ids, customer_ids)

    @api.model_create_multi
    def create(self, vals_list):
        company_id = self.env['res.company'].search([('production', '=', True)], limit=1)
        purchase_email = self.env['res.partner'].search([('ref', '=', 'INNKJOPSMAILEN')], limit=1)
        order_email = self.env['res.partner'].search([('ref', '=', 'ORDREMAILEN')], limit=1)
        purchase = super(PurchaseOrder, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        for po in purchase.filtered(lambda po: po.is_production and po.company_id == company_id):
            po.message_follower_ids.unlink()
            email = order_email if po.is_countertop_order else purchase_email
            po.message_subscribe(partner_ids=email.ids)
        return purchase
