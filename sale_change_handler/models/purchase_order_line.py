from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, readonly=False, store=True, compute='compute_product_qty')

    @api.depends('sale_line_id.product_uom_qty')
    def compute_product_qty(self):
        """ triggers when product qty is changed on sale order line """
        for pol in self:
            if pol._change_should_be_handled():
                # take other POL's in consideration when syncing
                old_qty = pol.product_qty
                other_pol_qty = 0.0
                for other_pol in pol.sale_line_id.purchase_line_ids:
                    if other_pol.state in ['draft', 'sent', 'to approve', 'purchase', 'done'] and other_pol.id != pol.id:
                        other_pol_qty += other_pol.product_qty

                # draft states
                if pol.state in ['draft', 'sent', 'to approve']: # and (pol.sale_line_id.product_uom_qty - old_qty - other_pol_qty) > 0.0:
                    # update quantity, make sure sol and pol are synchronized
                    # if several POLs, make sure the total amount is equal to the amount of the sale order line. If one purchase order goes below 0, cancel it and update the next one
                    # after discussion with purchase, we decided that this is an edge case that is handled manually. Further experiences might require this to be handled, but not for now
                    pol.product_qty = pol.sale_line_id.product_uom_qty - other_pol_qty

                    # if product on sale order line is set to 0, and the entire po is 0, and the po is in draft state, the po could be cancelled
                    if pol.state == 'draft' and not any(pol.order_id.order_line.filtered(lambda x: x.product_qty > 0.0)):
                        pol.order_id.button_cancel()
                # if this PO is in purchase/done state, and it does exist another one that is in draft, update the draft and let the confirmed one be left unchanged
                elif pol.state in ['purchase', 'done'] and not any(pol.sale_line_id.purchase_line_ids.filtered(lambda x: x.state in ['draft', 'sent', 'to approve'] and x.id != pol.id)):
                    # synchronize quantity if supplier is set up for it, otherwise adjust quantity and trigger activity when quantity is lower, or create new RFQ if quantity is higher
                    if pol.sale_line_id.product_uom_qty <= (pol.product_qty + other_pol_qty):
                        pol.product_qty = pol.sale_line_id.product_uom_qty - other_pol_qty
                    elif pol.order_id.partner_id.order_changes_should_be_synchronized:
                        # standard Odoo triggers new PO when quantity is bigger after confirmation. Force synchronization of original PO, and make sure the new PO is not created / cancelled / deleted, and generate activity
                        pol.product_qty = pol.sale_line_id.product_uom_qty - other_pol_qty
                        # add product of new po to this po (if new product)
                        # generate activity, not handled in Odoo standard when quantity is increased (normally just creates new PO)

                    else:
                        # sol has bigger quantity and pol, and po is confirmed, and the partner is not selected for forcing synchronization. Odoo standard creates new PO
                        _logger.info('sol has bigger quantity and pol, and po is confirmed. Odoo standard creates new PO, and the partner is not selected for forcing synchronization. Skipping custom logic')
                        continue

                # log to chatter
                if (old_qty + other_pol_qty) != pol.sale_line_id.product_uom_qty:
                    # feedback to purchaser if there is more than one POL for this sale order line
                    imp_msg = _('. Check other POs to control total quantity') if len(pol.sale_line_id.purchase_line_ids) > 1 else ''
                    pol.order_id.message_post(body=f'<div>Antall ble oppdatert<ul><li>Posisjon: {pol.position} antall: {old_qty + other_pol_qty} <i class="fa fa-long-arrow-right" style="vertical-align: middle;"/> {pol.product_qty + other_pol_qty}{imp_msg}</li></ul></div>')

    @api.model
    def _change_should_be_handled(self):
        # order_id is purchase order
        return self.order_id.is_production and self.sale_line_id
