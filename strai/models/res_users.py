from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    phone = fields.Char(related="partner_id.phone")
    initials = fields.Char(string="Initialer")

    @api.model_create_multi
    def create(self, vals_list):
        #Override create function to auto-add new users to the Real users group
        users = super(ResUsers, self).create(vals_list)

        for user in users:
            group_id = self.env.ref('strai.group_real_users').id
            user.write({'groups_id': [(4, group_id)]})
        return users
