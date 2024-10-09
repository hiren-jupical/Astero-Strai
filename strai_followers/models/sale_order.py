# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        return super(SaleOrder, self.with_context(selger_category_partners=True)).action_confirm()

    def _message_subscribe(self, partner_ids=None, subtype_ids=None, customer_ids=None):
        company_id = self.env['res.company'].search([('production', '=', True)], limit=1)
        if (self.env.context.get('search_default_my_quotation', False) or self.env.context.get('mark_so_as_sent', False) \
            or self.env.context.get('selger_category_partners', False)) \
            and not self.env.context.get('from_add_followers', False) \
            and self.is_production and self.company_id == company_id:
            return True
        return super()._message_subscribe(partner_ids, subtype_ids, customer_ids)

    @api.model_create_multi
    def create(self, vals_list):
        company_id = self.env['res.company'].search([('production', '=', True)], limit=1)
        order_email = self.env['res.partner'].search([('ref', '=', 'ORDREMAILEN')], limit=1)
        sales = super(SaleOrder, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        for sale in sales.filtered(lambda so: so.is_production and so.company_id == company_id):
            sale.message_follower_ids.unlink()
            email_ids = order_email.ids
            if sale.store_responsible_id.partner_id:
                email_ids += sale.store_responsible_id.partner_id.ids
            sale.message_subscribe(partner_ids=email_ids)
        return sales
