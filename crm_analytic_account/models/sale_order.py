from datetime import datetime
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                crm_lead = self.env['crm.lead'].browse(vals.get('opportunity_id'))
                if crm_lead:
                    analytic_account_id = crm_lead.analytic_account_id
                    if not analytic_account_id:
                        default_plan = self.env['account.analytic.plan'].search([('name', '=', 'Default')], limit=1)
                        analytic_account_id = self.env['account.analytic.account'].create({
                            'name': crm_lead.name,
                            'company_id': crm_lead.company_id.id,
                            'plan_id': default_plan.id
                        })
                        crm_lead.analytic_account_id = analytic_account_id

                    vals['analytic_account_id'] = analytic_account_id.id
                else:
                    partner = self.env['res.partner'].search([('id', '=', vals.get('partner_id'))])
                    company_prod = self.env['res.company'].sudo().search([('production', '=', True)], limit=1)
                    if vals['company_id'] == company_prod.id:
                        prod_crm = self.env['crm.lead'].with_company(company_prod.id).search([('partner_id', '=', partner.id), ('company_id', '=', company_prod.id), ('intercompany_lead', '=', True)])
                        if prod_crm:
                            vals['opportunity_id'] = prod_crm.id
                            vals['analytic_account_id'] = prod_crm.analytic_account_id.id
                    # cover situations where a crm lead does not exist in the store, and sale orders in production are
                    # not to intercompany customers or independent shops
                    if not vals.get('analytic_account_id'):
                        crm_lead = self.env['crm.lead'].create({
                            'name': f'{partner.display_name} - Manuell ordre {datetime.now().strftime("%d.%m.%Y")}',
                            'company_id': vals.get('company_id'),
                            'partner_id': partner.id,
                            'winner_lead_ref': vals.get('winner_reference') if not vals.get('is_production') else False
                        })

                        vals['analytic_account_id'] = crm_lead.analytic_account_id.id
                        vals['opportunity_id'] = crm_lead.id
        return super(SaleOrder, self).create(vals_list)
