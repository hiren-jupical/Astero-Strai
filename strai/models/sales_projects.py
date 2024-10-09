from odoo import api, fields, models
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class SalesProjects(models.Model):
    _name = 'sales.projects'
    _description = 'Sales Projects'
    _order = 'name asc'

    name = fields.Char()
    company_ids = fields.Many2many('res.company', default=lambda self: self.env['res.company'].search(['|', ('id', '=', self.env.company.id), ('production', '=', True)]))
    apartment_ids = fields.One2many('sales.projects.apartment', 'sales_project_id', string='Apartments')
    apartment_count = fields.Integer(compute='compute_apartment_count', string="Apartment Count")
    description = fields.Html()
    partner_id = fields.Many2one('res.users', string='Tilbudsansvarlig')
    developer_id = fields.Many2one('res.partner', domain="[('is_builder', '=', True)]")
    user_id = fields.Many2one('res.users', string='Prosjektleder', default=lambda self: self.env.user)
    account_group_id = fields.Many2one('account.analytic.plan')
    price_deal = fields.Text("Prisavtaler")
    status = fields.Selection([
        ('ongoing', 'Pågående'),
        ('closed', 'Ferdigstilt'),
    ], string='Status', copy=False, index=True, default='ongoing')

    @api.model_create_multi
    def create(self, vals_list):
        ress = super(SalesProjects, self).create(vals_list)
        for res in ress:
            # If there is more than one company id, the analytic account should always belong to the company that is not the main company
            if len(res.company_ids.ids) > 1:
                for cid in res.company_ids.ids:
                    if cid != 1:
                        company_id = cid
            else:
                company_id = res.company_ids.ids[0]
            vals = {'name': res['name']}
            account_group = self.env['account.analytic.plan'].create(vals)
            # To make the analytic account to be for company_id. As in 17 we do not have copmany_id in account.analytic.plan
            analytic_applicability = self.env['account.analytic.applicability'].create({
                'business_domain': 'general',
                'applicability': 'optional',
                'analytic_plan_id': account_group.id,
                'company_id': company_id,
            })
            res['account_group_id'] = account_group.id
        return ress

    def action_view_sales_projects_apartment(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('strai.act_sales_projects_2_project_apartment_all') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action

    def compute_apartment_count(self):
        apartment_data = self.env['sales.projects.apartment'].read_group(
            [('sales_project_id', 'in', self.ids)],
            ['sales_project_id', 'display_project_id:count'], ['sales_project_id'])
        result_wo_subtask = defaultdict(int)
        for data in apartment_data:
            result_wo_subtask[data['sales_project_id'][0]] += data['display_project_id']
        for project in self:
            project.apartment_count = result_wo_subtask[project.id]
        return result_wo_subtask

    def unlink(self):
        for project in self:
            apartment_ids = self.env['sales.projects.apartment'].search([('sales_project_id', '=', project.id)])
            for apartment in apartment_ids:
                apartment.unlink()
        return super(SalesProjects, self).unlink()
