from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class SalesProjectsApartment(models.Model):
    _name = 'sales.projects.apartment'
    _description = 'Sales Projects Apartment'
    _order = 'name asc'

    name = fields.Char()
    description = fields.Html()
    sales_project_id = fields.Many2one('sales.projects', string='Project', readonly=True)
    partner_id = fields.Many2one('res.partner')
    display_project_id = fields.Many2one('sales.projects', string='Display Project', index=True)
    user_ids = fields.Many2many('res.users', string='User')
    date_assign = fields.Datetime(string='Date assign')
    company_ids = fields.Many2many('res.company', string='Company', default=lambda self: self.env['res.company'].search(['|', ('id', '=', self.env.company.id), ('production', '=', True)]))
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account')
    sales_person_id = fields.Many2one('res.users', string='Selger')

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info(vals_list)
        for vals in vals_list:
            project_id = vals.get('sales_project_id') or self.env.context.get('default_project_id')
            if type(project_id) == int:
                project_id = self.env['sales.projects'].search([('id', '=', vals.get('sales_project_id') or self.env.context.get('default_project_id'))])
            if project_id and "company_ids" not in vals:
                vals["company_ids"] = self.env.company
            if vals.get('user_ids'):
                vals['date_assign'] = fields.Datetime.now()
            if project_id:
                vals['display_project_id'] = project_id.id
                vals['sales_project_id'] = project_id.id
                vals['company_ids'] = project_id.company_ids.ids
        apartments = super(SalesProjectsApartment, self).create(vals_list)
        for apartment in apartments:
            vals = {'name': apartment['name'],
                    'plan_id': apartment.sales_project_id.account_group_id.id if apartment.sales_project_id.account_group_id else False,
                    'company_id': apartment.analytic_account_id.company_id.id,
                    'account_analytic_type': 'project'}
            analytic_account_id = self.env['account.analytic.account'].create(vals)
            apartment.analytic_account_id = analytic_account_id.id
        return apartments
