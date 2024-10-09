# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
from odoo import models, fields, api, Command, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dispatch_advice_ids = fields.One2many('dispatch.advice.status', 'picking_id', string='Dispatch Advice')

    @api.model
    def update_peppol_delivery_response(self, delivery_json):
        cr = self.env.cr
        error_list, known_ids, unknown_ids, unknown_line_ids  = [], [], [], []
        message = _("Electronic Despatch Advice received from ")
        list_of_delivers = json.loads(delivery_json)
        for delivery in list_of_delivers:
            delivery_id = delivery.pop('document_id')
            (name, values), = delivery.items()
            doc = {name : delivery_id}
            transfer = self.search([('origin', '=', name), ('state', 'in', ['draft', 'assigned'])], limit=1)
            if transfer:
                try:
                    line_ids = transfer._process_delivery_lines(values.pop('lines'))
                    if line_ids:
                        values['dispatch_advice_ids']['status'] = 'exceptions' if \
                            any(x[1].get('status', '') == 'exception' for x in line_ids) else 'received'
                        values['dispatch_advice_ids']['dispatch_note']= self._get_product_supplier_code_table(line_ids)
                        values['dispatch_advice_ids'] = [Command.create(values.pop('dispatch_advice_ids'))]
                        values['move_ids_without_package'] = [Command.update(x[0].id, x[1]) for x in line_ids]
                        transfer.update(values)
                        transfer.message_post(body = message+transfer.partner_id.name)
                        known_ids.append(doc)
                    else:
                        unknown_line_ids.append(doc)
                except Exception:
                    transfer.status = 'exceptions'
                    error_list.append(doc)
                finally:
                    cr.commit()
            else:
                unknown_ids.append(doc)
        res = {"unknown_ids": unknown_ids, "unknown_line_ids": unknown_line_ids, 'known_ids': known_ids, 'error_list': error_list}
        return res

    def _process_delivery_lines(self, lines):
        update_line_list = []
        for line in lines:
            po_line_id = line.pop('purchase_line_id')
            line_id = self.move_ids_without_package.filtered(lambda line:line.purchase_line_id.peppol_line_id == po_line_id)
            if line_id:
                line.update(**line_id[0]._prepared_status_values(line))
                update_line_list.append((line_id[0], line))
            else:
                return False
        return update_line_list

    def _get_product_supplier_code_table(self, line_ids):
        product_name = _('Product Name')
        supplier_code = _('Supplier Code')
        table = f"<table class='table table-bordered o_table'><th>{product_name}</th><th>{supplier_code}</th>"
        for move_id, values in line_ids:
            table+=f"<tr><td>{move_id.product_id.with_context(lang=move_id.picking_id.partner_id.lang).display_name}</td><td>{values.pop('supplier_code')}</td></tr>"
        table+="</table>"
        return table
