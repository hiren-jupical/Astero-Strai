# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        results = super()._notify_get_recipients(message, msg_vals, **kwargs)
        #Find purchase order and send mesage to purchase order chatter.
        model = self.env.context.get('active_model')
        if model and model == 'sale.order':
            sale_order = self.env['sale.order'].sudo().browse(self.env.context.get('active_id'))
            if sale_order:
                if sale_order.client_order_ref:
                    purchase_order = self.env['purchase.order'].sudo().search([('name', '=', sale_order.client_order_ref)], limit=1)
                    if purchase_order and message:
                        for attachment in message.attachment_ids:
                            attachment.allow_multicompany = True
                        po_message = message.copy()
                        data = {'res_id': purchase_order.id,
                                'model': purchase_order._name,
                                'record_name': purchase_order.name,
                                }
                        po_message.write(data)
                        purchase_order.supplier_confirmed = True
        template_id = self.env.ref('strai_email_so_to_store.email_template_for_so_to_store', raise_if_not_found=False)
        if template_id and msg_vals.get('partner_ids') and self.env.context.get('default_template_id') == template_id.id:
            data = []
            for result in results:
                if result.get('id') in msg_vals.get('partner_ids'):
                    result['notif'] = 'email'
                    data.append(result)
            return data
        return results