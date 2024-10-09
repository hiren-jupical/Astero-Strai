# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from lxml.builder import E
from odoo import models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super(models.Model,self)._get_view(view_id, view_type, **options)
        if self.env['account.analytic.plan'].check_access_rights('read', raise_exception=False):
            project_plan, other_plans = self.env['account.analytic.plan']._get_all_plans()

            # Find main account nodes
            account_node = next(iter(arch.xpath('//field[@name="account_id"]')), None)
            account_filter_node = next(iter(arch.xpath('//filter[@name="account_id"]')), None)

            # Force domain on main account node as the fields_get doesn't do the trick
            if account_node is not None and view_type == 'search':
                account_node.attrib['domain'] = f"[('plan_id', 'child_of', {project_plan.id})]"

            # If there is a main node, append the ones for other plans
            if account_node is not None or account_filter_node is not None:
                for plan in other_plans[::-1]:
                    fname = plan._column_name()
                    if account_node is not None and view_type == 'tree':
                        account_node.addnext(E.field(name=fname, domain=f"[('plan_id', 'child_of', {plan.id})]", optional="hide"))
                    if account_node is not None and view_type == 'form':
                        account_node.addnext(E.field(name=fname, domain=f"[('plan_id', 'child_of', {plan.id})]", invisible="true"))
                    if account_filter_node is not None:
                        account_filter_node.addnext(E.filter(name=fname, context=f"{{'group_by': '{fname}'}}"))
        return arch, view
