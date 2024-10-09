from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    analytic_account_id = fields.Many2one('account.analytic.account', company_dependent=True)
    intercompany_lead = fields.Boolean(default=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('analytic_account_id'):
                vals['analytic_account_id'] = self.get_analytic_account(vals['name'], vals['company_id'])
        return super(CrmLead, self).create(vals_list)

    def get_analytic_account(self, crm_name, analytic_company):
        company = analytic_company if isinstance(analytic_company, int) else analytic_company.id
        name = crm_name
        if not name:
            name = "{0}".format(self.name)
        if not self.with_company(company).analytic_account_id:
            # assign default plan
            default_plan = self.env['account.analytic.plan'].search([('name', '=', 'Default')], limit=1)
            analytic_account = self.env['account.analytic.account'].create({'name': name,
                                                                            'company_id': company,
                                                                            'plan_id': default_plan.id})
        return analytic_account
