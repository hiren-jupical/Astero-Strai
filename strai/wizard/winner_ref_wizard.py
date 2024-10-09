from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger=logging.getLogger(__name__)


class WinnerRefWizard(models.TransientModel):
    _name = 'winner.ref.wizard'
    _description = 'Winner Ref Wizard'

    sale_order = fields.Many2one('sale.order')
    winner_reference = fields.Char(store=True)
    environment = fields.Char()
    environment_original = fields.Char()
    alternative = fields.Char()

    def create(self, values):
        res = super(WinnerRefWizard, self).create(values)
        if values.get('environment'):
            res.update({'environment_original': values['environment']})
        return res

    def _change_environment(self):
        if self.environment and self.environment.isnumeric() == True:
            winner_ref = self.winner_reference.replace(f'/{self.environment_original}/', f'/{self.environment}/', 1)
            return self._change_alternative(winner_ref)
        else:
            raise UserError(_('You did not input anything in the environment field, or your input was not a number'))

    def _change_alternative(self, winner_ref):
        if self.alternative and self.alternative.isnumeric() == True:
            last_delimiter_index = winner_ref.rfind('/')
            new_winner_ref = winner_ref[:last_delimiter_index] + f"/{self.alternative}"
            return new_winner_ref
        else:
            raise UserError(_('You did not input anything in the alternative field, or your input was not a number'))

    def get_winner_reference(self):
        return self._change_environment()

    def save(self):
        if self.winner_reference:
            original_winner_ref = self.sale_order.winner_reference
            new_winner_ref = self.get_winner_reference()
            other_sale_order_with_new_winner_ref = self.env['sale.order'].search([('winner_reference', '=', new_winner_ref), ('company_id', '=', self.sale_order.company_id.id)])
            if other_sale_order_with_new_winner_ref:
                raise UserError(_('This Winner reference already exists in another quotation'))

            self.sale_order.winner_reference = new_winner_ref
            self.sale_order.message_post(body=_("Winner-referanse endret fra %s til %s", original_winner_ref, self.sale_order.winner_reference))
            if original_winner_ref != new_winner_ref:
                self.sale_order.winner_file_new_version_required = True
            _logger.info('Winner reference changed')
