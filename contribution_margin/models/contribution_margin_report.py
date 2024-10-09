# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class ContributionMarginReport(models.Model):
    _name = 'contribution.margin.report'
    _description = "Contribution Margin Report"
    _auto = False
    _rec_name = 'account_id'
    _order = 'account_id desc'

    account_id = fields.Many2one('account.analytic.account', string='Kunde')
    status = fields.Selection([
        ('checked', 'Checked'),
        ('not_checked', 'Not Checked'),
        ('checked_and_changed', 'Checked & Changed'),
    ], default='not_checked', compute="_compute_status_and_comment", search='_search_status')
    comment = fields.Char(string='Kommentar', compute="_compute_status_and_comment")
    company_id = fields.Many2one('res.company', string='Company')
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency")
    group_id = fields.Many2one('account.analytic.plan', string="Group")
    account_analytic_type = fields.Selection(selection=[
        ('standard', 'Standard'),
        ('financial', 'Financial'),
        ('exhibition', 'Exhibition'),
        ('project', 'Project')], string='Account Analytic Type')
    flyt_first_update = fields.Date(string='First Entry', help="First posted move line date")
    flyt_last_update = fields.Date(string='Last Update', help="Last posted move line date")
    move_id =  fields.Many2one('account.move', string='Invoice Moves')
    order_type = fields.Selection(related="move_id.order_type", string='Ordretype')
    user_id = fields.Many2one('res.users', related="move_id.invoice_user_id", string="Selger")

    # product types
    kitchen = fields.Float(string='Kjøkken %')
    kitchen_amount = fields.Float(string='Kjøkken Kr')
    bath = fields.Float(string='Bad %')
    bath_amount = fields.Float(string='Bad Kr')
    wardrobe = fields.Float(string='Garderobe %')
    wardrobe_amount = fields.Float(string='Garderobe Kr')
    laundry_room = fields.Float(string='Vaskerom %')
    laundry_room_amount = fields.Float(string='Vaskerom Kr')

    credit = fields.Float(string='Salg')
    debit = fields.Float(string='Kjøp')

    coverage = fields.Float(string='Dekning i kr')
    coverage_percent = fields.Float(string='Dekning i %')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        groups = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        context = dict(self.env.context or {})
        if context.get('params') and context.get('params').get('model') == 'contribution.margin.report':
            for group in groups:
                if 'coverage_percent' in group:
                    if group.get('credit') > 0:
                        group['coverage_percent'] = (group['coverage'] / group['credit']) * 100
                    else:
                        group['coverage_percent'] = 0.0
        return groups

    def _search_status(self, operator, value):
        """
        Added this search method as to use the field `status` in the domain for filtering purpose.
        """
        accounts = self.env['contribution.margin.user.data'].search_fetch(
            [('custom_status', operator, value)], ['analytic_account_id'])
        return [('account_id', 'in', accounts.analytic_account_id.ids)]

    def _compute_status_and_comment(self):
        for rec in self:
            related_user_data = rec.get_related_report_data()
            if related_user_data:
                rec.comment = related_user_data.comment
                if related_user_data.custom_credit == rec.credit and related_user_data.custom_debit == rec.debit and related_user_data.custom_status == 'checked':
                    related_user_data.custom_status = 'checked'
                elif (related_user_data.custom_credit != rec.credit or related_user_data.custom_debit != rec.debit) and related_user_data.custom_status == 'checked':
                    related_user_data.custom_status = 'checked_and_changed'
                
                rec.status = related_user_data.custom_status
            else:
                rec.status = 'not_checked'
                rec.comment = ''

    def get_related_report_data(self):
        if not self.account_id.contribution_data_ids:
            return self.env['contribution.margin.user.data'].create({
                'custom_credit': self.credit,
                'custom_debit': self.debit,
                'analytic_account_id': self.account_id.id,
                'company_id': self.account_id.company_id.id,
            })
        else:
            return self.account_id.contribution_data_ids[0]

    @api.onchange('comment')
    def _onchange_comment(self):
        related_user_data = self.get_related_report_data()
        related_user_data.comment = self.comment if related_user_data else False

    def action_update_status_checked(self):
        for rec in self:
            report_data = rec.get_related_report_data()
            report_data.custom_status = 'checked'
            report_data.custom_credit = rec.credit
            report_data.custom_debit = rec.debit

    def action_update_status_not_checked(self):
        for rec in self:
            report_data = rec.get_related_report_data()
            report_data.custom_status = 'not_checked'

    def _query(self, fields='', from_clause='', where=''):
        # all the sales and purchase entry is in seprate account so comment this for now
        # credit_account = self.env['account.account'].search([('user_type_id.name', '=', 'Income')], limit=1)
        # debit_account = self.env['account.account'].search([('user_type_id.name', '=', 'Expenses')], limit=1)

        return '''
        WITH analytic_account AS (
            SELECT (Jsonb_object_keys(analytic_distribution) :: INT) AS analytic_account_id,
                   id AS move_line_id
            FROM account_move_line
            WHERE analytic_distribution IS NOT NULL
                  AND parent_state = 'posted'
                  AND move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'entry')
        )

        SELECT DISTINCT ON (a.analytic_account_id)
            MIN(line.id) as id,
            a.analytic_account_id as account_id,
            MAX(CASE WHEN line.move_type in ('out_invoice', 'out_refund') THEN line.move_id ELSE 0 END) as move_id,
            SUM(
                CASE WHEN line.move_type in ('out_invoice', 'out_refund') THEN
                    CASE WHEN line.credit > 0 THEN line.credit
                         WHEN line.debit > 0 THEN -(line.debit) END
                    WHEN line.move_type in ('entry') THEN
                    CASE WHEN account.account_type in ('income') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END
                        ELSE 0
                    END
                END
            ) as credit,
            SUM(
                CASE WHEN line.move_type in ('in_invoice', 'in_refund') THEN
                    CASE WHEN line.debit > 0 THEN line.debit
                         WHEN line.credit > 0 THEN -(line.credit) END
                    WHEN line.move_type in ('entry') THEN
                    CASE WHEN account.account_type in ('expense') THEN
                        CASE WHEN line.debit > 0 THEN line.debit
                            WHEN line.credit > 0 THEN -(line.credit) END
                        ELSE 0
                    END
                END
            ) as debit,
            SUM(
                CASE WHEN line.move_type in ('out_invoice', 'in_refund') THEN
                    CASE WHEN line.credit > 0 THEN line.credit
                         WHEN line.debit > 0 THEN -(line.debit) END
                    
                    WHEN line.move_type in ('in_invoice', 'out_refund') THEN
                    CASE WHEN line.debit > 0 THEN -(line.debit)
                        WHEN line.credit > 0 THEN line.credit END

                    WHEN line.move_type in ('entry')
                    THEN CASE WHEN account.account_type in ('income') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END

                        WHEN account.account_type in ('expense') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) as coverage,
            SUM(
                CASE WHEN line.move_type in ('out_invoice', 'out_refund') THEN
                    CASE WHEN line.credit > 0 THEN line.credit
                         WHEN line.debit > 0 THEN -(line.debit) END
                    
                    WHEN line.move_type in ('in_invoice', 'in_refund') THEN
                    CASE WHEN line.debit > 0 THEN -(line.debit)
                        WHEN line.credit > 0 THEN line.credit END

                    WHEN line.move_type in ('entry')
                    THEN CASE WHEN account.account_type in ('income') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END

                        WHEN account.account_type in ('expense') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) / NULLIF(((
                    SUM(CASE WHEN line.move_type in ('out_invoice', 'out_refund') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END
                            WHEN line.move_type in ('entry') THEN
                            CASE WHEN account.account_type in ('income') THEN
                                CASE WHEN line.credit > 0 THEN line.credit
                                    WHEN line.debit > 0 THEN -(line.debit) END
                                ELSE 0
                            END
                            ELSE 0
                        END
                ))), 0) * 100
             as coverage_percent,

            SUM(
                CASE WHEN line.product_type_id = 1 and line.move_type in ('out_invoice', 'out_refund') THEN
                    CASE WHEN line.credit > 0 THEN line.credit
                         WHEN line.debit > 0 THEN -(line.debit) END

                    WHEN line.product_type_id = 1 and line.move_type in ('in_invoice', 'in_refund') THEN
                    CASE WHEN line.debit > 0 THEN -(line.debit)
                        WHEN line.credit > 0 THEN line.credit END

                    WHEN line.product_type_id = 1 and line.move_type in ('entry')
                    THEN CASE WHEN account.account_type in ('income') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END

                        WHEN line.product_type_id = 1 and account.account_type in ('expense') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) / NULLIF(((
                    SUM(CASE WHEN line.product_type_id = 1 and line.move_type in ('out_invoice', 'out_refund') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END
                            WHEN line.move_type in ('entry') THEN
                            CASE WHEN line.product_type_id = 1 and account.account_type in ('income') THEN
                                CASE WHEN line.credit > 0 THEN line.credit
                                    WHEN line.debit > 0 THEN -(line.debit) END
                                ELSE 0
                            END
                            ELSE 0
                        END
                ))), 0) * 100
             as kitchen,

            SUM(
                CASE WHEN line.product_type_id = 1
                    THEN CASE WHEN line.move_type in ('out_invoice', 'out_refund') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END
                        
                        WHEN line.move_type in ('in_invoice', 'in_refund') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END

                        WHEN line.move_type in ('entry') THEN
                        CASE WHEN account.account_type in ('income') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END
                            WHEN account.account_type in ('expense') THEN
                            CASE WHEN line.debit > 0 THEN -(line.debit)
                                WHEN line.credit > 0 THEN line.credit END
                            ELSE 0
                        END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) as kitchen_amount,
            SUM(
                CASE WHEN line.product_type_id = 2
                    THEN CASE WHEN line.move_type in ('out_invoice', 'out_refund') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END

                        WHEN line.move_type in ('in_invoice', 'in_refund') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END

                        WHEN line.move_type in ('entry')
                        THEN CASE WHEN account.account_type in ('income') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END

                            WHEN account.account_type in ('expense') THEN
                            CASE WHEN line.debit > 0 THEN -(line.debit)
                                WHEN line.credit > 0 THEN line.credit END
                            ELSE 0
                        END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) as bath_amount,

            SUM(
                CASE WHEN line.product_type_id = 2 and line.move_type in ('out_invoice', 'out_refund') THEN
                    CASE WHEN line.credit > 0 THEN line.credit
                         WHEN line.debit > 0 THEN -(line.debit) END

                    WHEN line.product_type_id = 2 and line.move_type in ('in_invoice', 'in_refund') THEN
                    CASE WHEN line.debit > 0 THEN -(line.debit)
                        WHEN line.credit > 0 THEN line.credit END

                    WHEN line.product_type_id = 2 and line.move_type in ('entry')
                    THEN CASE WHEN account.account_type in ('income') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END

                        WHEN line.product_type_id = 2 and account.account_type in ('expense') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) / NULLIF(((
                    SUM(CASE WHEN line.product_type_id = 2 and line.move_type in ('out_invoice', 'out_refund') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END
                            WHEN line.move_type in ('entry') THEN
                            CASE WHEN line.product_type_id = 2 and account.account_type in ('income') THEN
                                CASE WHEN line.credit > 0 THEN line.credit
                                    WHEN line.debit > 0 THEN -(line.debit) END
                                ELSE 0
                            END
                            ELSE 0
                        END
                ))), 0) * 100
             as bath,

            SUM(
                CASE WHEN line.product_type_id = 3 and line.move_type in ('out_invoice', 'out_refund') THEN
                    CASE WHEN line.credit > 0 THEN line.credit
                         WHEN line.debit > 0 THEN -(line.debit) END

                    WHEN line.product_type_id = 3 and line.move_type in ('in_invoice', 'in_refund') THEN
                    CASE WHEN line.debit > 0 THEN -(line.debit)
                        WHEN line.credit > 0 THEN line.credit END

                    WHEN line.product_type_id = 3 and line.move_type in ('entry')
                    THEN CASE WHEN account.account_type in ('income') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END

                        WHEN line.product_type_id = 3 and account.account_type in ('expense') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) / NULLIF(((
                    SUM(CASE WHEN line.product_type_id = 3 and line.move_type in ('out_invoice', 'out_refund') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END
                            WHEN line.move_type in ('entry') THEN
                            CASE WHEN line.product_type_id = 3 and account.account_type in ('income') THEN
                                CASE WHEN line.credit > 0 THEN line.credit
                                    WHEN line.debit > 0 THEN -(line.debit) END
                                ELSE 0
                            END
                            ELSE 0
                        END
                ))), 0) * 100
             as wardrobe,

            SUM(
                CASE WHEN line.product_type_id = 3
                    THEN CASE WHEN line.move_type in ('out_invoice', 'in_refund') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END
                        
                        WHEN line.move_type in ('in_invoice', 'out_refund') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END

                        WHEN line.move_type in ('entry')
                        THEN CASE WHEN account.account_type in ('income') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END

                            WHEN account.account_type in ('expense') THEN
                            CASE WHEN line.debit > 0 THEN -(line.debit)
                                WHEN line.credit > 0 THEN line.credit END
                            ELSE 0
                        END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) as wardrobe_amount,
            SUM(
                CASE WHEN line.product_type_id = 4
                    THEN CASE WHEN line.move_type in ('out_invoice', 'in_refund') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END

                        WHEN line.move_type in ('in_invoice', 'out_refund') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END

                        WHEN line.move_type in ('entry')
                        THEN CASE WHEN account.account_type in ('income') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END

                            WHEN account.account_type in ('expense') THEN
                            CASE WHEN line.debit > 0 THEN -(line.debit)
                                WHEN line.credit > 0 THEN line.credit END
                            ELSE 0
                        END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) as laundry_room_amount,

            SUM(
                CASE WHEN line.product_type_id = 4 and line.move_type in ('out_invoice', 'out_refund') THEN
                    CASE WHEN line.credit > 0 THEN line.credit
                         WHEN line.debit > 0 THEN -(line.debit) END

                    WHEN line.product_type_id = 4 and line.move_type in ('in_invoice', 'in_refund') THEN
                    CASE WHEN line.debit > 0 THEN -(line.debit)
                        WHEN line.credit > 0 THEN line.credit END

                    WHEN line.product_type_id = 4 and line.move_type in ('entry')
                    THEN CASE WHEN account.account_type in ('income') THEN
                        CASE WHEN line.credit > 0 THEN line.credit
                            WHEN line.debit > 0 THEN -(line.debit) END

                        WHEN line.product_type_id = 4 and account.account_type in ('expense') THEN
                        CASE WHEN line.debit > 0 THEN -(line.debit)
                            WHEN line.credit > 0 THEN line.credit END
                        ELSE 0
                    END
                    ELSE 0
                END
            ) / NULLIF(((
                    SUM(CASE WHEN line.product_type_id = 4 and line.move_type in ('out_invoice', 'out_refund') THEN
                            CASE WHEN line.credit > 0 THEN line.credit
                                WHEN line.debit > 0 THEN -(line.debit) END
                            WHEN line.move_type in ('entry') THEN
                            CASE WHEN line.product_type_id = 4 and account.account_type in ('income') THEN
                                CASE WHEN line.credit > 0 THEN line.credit
                                    WHEN line.debit > 0 THEN -(line.debit) END
                                ELSE 0
                            END
                            ELSE 0
                        END
                ))), 0) * 100
             as laundry_room,

            line.company_id as company_id,
            MIN(line.date) as flyt_first_update,
            MAX(line.date) as flyt_last_update,
            aaa.plan_id as group_id,
            aaa.account_analytic_type as account_analytic_type
            FROM
                account_move_line line
            INNER JOIN res_company company ON company.id = line.company_id
            INNER JOIN account_move move ON move.id = line.move_id
            INNER JOIN analytic_account a ON a.move_line_id = line.id
            INNER JOIN account_analytic_account aaa ON aaa.id = a.analytic_account_id
            INNER JOIN res_currency currency ON currency.id = company.currency_id
            INNER JOIN account_account account ON account.id = line.account_id
            WHERE
                a.analytic_account_id IS NOT NULL
                AND line.parent_state = 'posted'
                AND line.company_id = move.company_id
                AND line.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'entry')
            GROUP BY aaa.id, aaa.account_analytic_type, a.analytic_account_id, line.company_id, currency.decimal_places
        '''

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
