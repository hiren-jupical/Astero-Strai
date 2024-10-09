from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    competitor_id = fields.Many2one('res.partner', string="Lost to Competitor", domain="[('category_id', '=', 'Competitor')]")

    @api.constrains('lost_reason_id')
    def check_reason(self):
        for rec in self:
            if not rec.lost_reason_id:
                raise ValidationError(_('You must select a reason'))
