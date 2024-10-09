from odoo import api, fields, models
import logging
import sys
sys.setrecursionlimit(10000)

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    winner_alone = fields.Char(compute='_computer_winner_alone')
    winner_lead_ref = fields.Char(string='Winner Referense')
    crm_name = fields.Char(string='Lead name')

    def action_view_sale_order(self):
        action = super(CrmLead, self).action_view_sale_order()
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'not in', ('draft', 'sent', 'signed', 'reserved', 'cancel'))]
        orders = self.mapped('order_ids').filtered(lambda l: l.state not in ('draft', 'sent', 'signed', 'reserved', 'cancel'))
        if len(orders) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = orders.id
        return action

    def action_view_sale_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['context'] = {
            'search_default_draft': 0,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id
        }
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent', 'signed', 'reserved'])]
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent', 'signed', 'reserved'))
        _logger.info(quotations)
        _logger.info(len(quotations))
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order', 'order_ids.company_id')
    def _compute_sale_data(self):
        res = super(CrmLead, self)._compute_sale_data()
        for lead in self:
            total = 0.0
            quotation_cnt = 0
            sale_order_cnt = 0
            company_currency = lead.company_currency or self.env.company.currency_id
            for order in lead.order_ids:
                if order.state in ('draft', 'sent', 'signed', 'reserved'):
                    quotation_cnt += 1
                if order.state not in ('draft', 'sent', 'signed', 'reserved', 'cancel'):
                    sale_order_cnt += 1
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.quotation_count = quotation_cnt
            lead.sale_order_count = sale_order_cnt
        return res

    # For dividing Winner reference into Company info (X/[...]) and Winner reference ([...]/YYY...)
    def _computer_winner_alone(self):
        for record in self:
            if record.winner_lead_ref and '/' in record.winner_lead_ref:
                new_text = record.winner_lead_ref.split("/")
                record.winner_alone = new_text[1]

            else:
                record.winner_alone = record.winner_lead_ref

    def _create_lead(self, order_data, partner_id, user_id):
        if order_data['order_version']:
            existing_lead = self.env['crm.lead'].search([('name', '=', partner_id.name)])
        else:
            existing_lead = self.env['crm.lead'].search([('winner_lead_ref', '=', order_data['winner_lead_ref'])])
        
        if existing_lead:
            return existing_lead.id

        values = self._prepare_values(order_data, partner_id, user_id)

        lead = self.create(values)
        lead.convert_opportunity(partner_id)
        current_user_mail = self.env.user.email
        self.env['sale.order'].remove_as_follower(lead, current_user_mail)
        return lead.id

    def _prepare_values(self, order_data, partner_id, user_id):
        if order_data['crm_name']:
            return {
                'name': order_data['crm_name'],
                'partner_id': partner_id.id,
                'company_id': order_data['sales_company'],
                'user_id': user_id,
                'winner_lead_ref': order_data['winner_lead_ref']
            }

        else:
            return {
                'name': order_data['winner_lead_ref'],
                'partner_id': partner_id.id,
                'company_id': order_data['sales_company'],
                'user_id': user_id,
                'winner_lead_ref': order_data['winner_lead_ref']
            }
