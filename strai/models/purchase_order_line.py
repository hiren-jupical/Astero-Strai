from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    strai_discount = fields.Float(string='Discount (%)', digits='Discount', store=True, readonly=False)
    position = fields.Integer(string="pos", compute='compute_position_number', store=True)
    fixed_position = fields.Integer()

    order_type = fields.Selection(string="Order Type", related='order_id.order_type')
    catalogue_price = fields.Monetary()
    activate_onchange_price = fields.Boolean(default=False)
    vendor_price = fields.Monetary()
    base_vendor_discount = fields.Float()

    so_line_id = fields.Char(readonly=True)

    price_before_discount = fields.Monetary(readonly=True, store=True)
    price_changed_manually = fields.Boolean(default=False)

    rule_base_purchase_price = fields.Boolean(default=False)

    winner_catalogue_id = fields.Many2one('winner.catalogue', string="Winner catalogue", required=False)

    @api.depends('order_id.origin')
    def compute_position_number(self):
        for line in self:
            if not line.position or line.position == 0:
                if line.sale_line_id:
                    line.position = line.sale_line_id.position
                    break
                picking_id = self.env['stock.picking'].search([('origin', '=', line.order_id.origin)])
                if picking_id:
                    for move_id in picking_id.move_ids_without_package:
                        if line.id in move_id.created_purchase_line_ids.ids:
                            line.position = move_id.sale_line_id.position
                            break
            if not line.position:
                line.position = 0

    def create(self, vals):
        res = super(PurchaseOrderLine, self).create(vals)
        for line in res:
            if line.sale_line_id:
                line.position = line.sale_line_id.position
                line.name = line.sale_line_id.name
            line.get_neighbour_sections()
        return res

    # Pulls prices for lines from SO to PO
    @api.model
    def _prepare_add_missing_fields(self, values):
        res = super()._prepare_add_missing_fields(values)
        discount = values.get('strai_discount')
        already_set_price_unit = values.get('price_unit')
        rule_base_purchase_price = values.get('rule_base_purchase_price')
        if values.get('sale_line_id'):
            sale_line = self.env['sale.order.line'].browse(values['sale_line_id'])
            price_before_discount = max(sale_line.catalogue_price, sale_line.price_unit)
            if price_before_discount and discount:
                price_unit_discounted = price_before_discount * (1 - discount / 100.0)
            elif price_before_discount:
                price_unit_discounted = price_before_discount
            else:
                price_unit_discounted = already_set_price_unit

            res.update({
                'catalogue_price': sale_line.catalogue_price,
                'so_line_id': sale_line.id,
                'price_before_discount': max(sale_line.catalogue_price, sale_line.price_unit),
                'price_unit': price_unit_discounted if not rule_base_purchase_price else already_set_price_unit,
                'winner_catalogue_id': sale_line.winner_catalogue_id.id
            })
            if not self.env.company.production or values.get('price_unit') == 0.0:
                res.update({
                    'price_unit': price_unit_discounted if price_unit_discounted else max(sale_line.catalogue_price, sale_line.price_unit)
                })
        return res

    # Pulls catalogue price from PO to intercompany SO
    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        res = super()._prepare_sale_order_data(name, partner, company, direct_delivery_address)
        res.update({
            'catalogue_price': self.catalogue_price,
            'price_unit': max(self.catalogue_price, self.price_unit)
        })
        return res

    _sql_constraints = [
        (
            "discount_limit",
            "CHECK (strai_discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    # Purchase line id is added to sale order lines to prevent function from running twice on the same product for no reason with wrong values
    # Function would not work when duplicating sale order because purchase line id would also be dublicated.
    # Solved by passing purchase_line_id (po_id) into default paramater in this function.
    @api.model
    def _prepare_purchase_order_line_from_so_line(self, po, product_id):
        sale_order_names = po.origin.split(', ')
        sale_orders = self.env['sale.order'].search([('name', 'in', sale_order_names)])
        for order in sale_orders:
            for line in order.order_line:
                if line.product_id == product_id and not line.purchase_line_id:
                    line.purchase_line_id = po.id
                    return {"price_unit": line.price_unit,
                            "catalogue_price": line.catalogue_price,
                            "price_before_discount": line.price_unit,
                            "winner_catalogue_id": line.winner_catalogue_id.id}
        return {}

    @api.onchange('price_unit')
    def _onchange_price_unit_for_discount(self):
        if self.activate_onchange_price:
            self.delete_sale_order_purchase_line_id()
            self.strai_discount = self._calculate_reverse_discount(self._origin.vendor_price, self._origin.base_vendor_discount, self._origin.order_id, self.product_id, self.price_unit)

    def delete_sale_order_purchase_line_id(self):
        sale_order_names = self._origin.order_id.origin.split(', ')
        sale_orders = self.env['sale.order'].search([('name', 'in', sale_order_names)])
        for order in sale_orders:
            for line in order.order_line:
                line.purchase_line_id = None

    # Function used to fetch Section lines from the original SO when new PO lines are created.
    # It specifically looks at those lines that have a sequence +/- 1 of its own (assigned via the confirm action in this modules sale.py)
    # in order to avoid over-reliance on potentially irregular sequencing or id sorting; instead going solely by how the SO is ordered at the point of confirmation.
    # Note the function is called in POL's create function.
    def get_neighbour_sections(self):
        po = self.order_id
        so = self.sale_order_id
        self_so_line = self.sale_line_id
        self.sequence = self_so_line.sequence
        
        line_section = False
        current_line_section = False
        comments = []
        last_line_was_comment = False
        for line in so.order_line:
            # find correct line section
            if line.display_type == 'line_section':
                current_line_section = line

            if not line_section and line.sequence == self.sequence and current_line_section:
                line_section = current_line_section

            # find comments that belong to this product
            if line.sequence > self.sequence and line.display_type == 'line_note':
                comments.append(line)
                last_line_was_comment = True
            elif not last_line_was_comment and line.sequence >= self.sequence + 1:
                break
            else:
                last_line_was_comment = False
        
        lines = comments
        if line_section:
            lines += [line_section]

        for line in lines:
            if line not in po.order_line.sale_line_id:
                lines.append(line)
                po.order_line.create({
                    'name': line.name,
                    'display_type': line.display_type,
                    'sequence': line.sequence,
                    'sale_line_id': line.id,
                    'product_qty': 0,
                    'order_id': po.id,
                    'product_id': False,
                    'price_unit': 0,
                    'product_uom_qty': 0,
                    'product_uom': False,
                    'date_planned': False,
                })

    # This method is not getting called from anywhere.
    # def _prepare_stock_move(self, picking, price_unit, product_uom_qty, product_uom):
    #     res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
    #     if self.so_line_id:
    #         res.update({
    #             'original_sale_order_line': self.so_line_id
    #         })
    #     return res

    # This opdates all products that are the type of service on the related SO. When a PO has recieved products
    def write(self, values):
        if 'qty_delivered' in values:
            if 'sale_order_id' in self:
                for line in self.sale_order_id.order_line:
                    if line.product_type == 'service':
                        line.write({'qty_delivered': line.product_uom_qty})
        return super(PurchaseOrderLine, self).write(values)

    # TODO: check
    # override standard function. Error when purchasing from Strai/lager and not HUB/lager. For these products stock will pile up in Strai, and go negative in Hub indefinitely.
    # a better solution should be found
    def _check_orderpoint_picking_type(self):
        pass
