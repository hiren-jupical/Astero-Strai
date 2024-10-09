# -*- coding: utf-8 -*-
##############################################################################
#
#    Flyt Consulting AS
#    Copyright (C) 2019-Today Flyt Consulting AS.(<https://www.flytconsulting.no>).
#    Author: Flyt Consulting AS. (<https://www.flytconsulting.no>) 
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models
from markupsafe import Markup

class SaleOrderExt(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        vals_keys = vals.keys()
        so_obj = self.env['sale.order']
        for rec in self:
            message = ""
            if rec.type == "delivery":
            
                if 'name' in vals_keys:
                    name = vals.get('name', False)
                    if rec.name:
                        message += rec.name  +"&nbsp;-->&nbsp;"
                    else:
                        message += "None &nbsp;-->&nbsp;"
                    
                    if name:
                        message += name + " &nbsp;(name)<br/>"
                    else:
                        message +=  "None &nbsp;(name)<br/>"
                
                if 'street' in vals_keys:
                    street = vals.get('street', False)
                    if rec.street:
                        message += rec.street  +"&nbsp;-->&nbsp;"
                    else:
                        message += "None &nbsp;-->&nbsp;"
                    
                    if street:
                        message += street + " &nbsp;(street)<br/>"
                    else:
                        message +=  "None &nbsp;(street)<br/>"

                if 'street2' in vals_keys:
                    street2 = vals.get('street2', False)
                    if rec.street2:
                        message += rec.street2  +"&nbsp;-->&nbsp;"
                    else:
                        message += "None &nbsp;-->&nbsp;"
                    
                    if street2:
                        message += street2 + " &nbsp;(street2)<br/>"
                    else:
                        message +=  "None &nbsp;(street2)<br/>"

                if 'city' in vals_keys:
                    city = vals.get('city', False)
                    if rec.city:
                        message += rec.city  +"&nbsp;-->&nbsp;"
                    else:
                        message += "None &nbsp;-->&nbsp;"
                    
                    if city:
                        message += city + " &nbsp;(city)<br/>"
                    else:
                        message +=  "None &nbsp;(city)<br/>"

                if 'zip' in vals_keys:
                    zip = vals.get('zip', False)
                    if rec.zip:
                        message += rec.zip  +"&nbsp;-->&nbsp;"
                    else:
                        message += "None &nbsp;-->&nbsp;"
                    
                    if zip:
                        message += zip + " &nbsp;(zip)<br/>"
                    else:
                        message +=  "None &nbsp;(zip)<br/>"

                if 'country_id' in vals_keys:
                    country_id = vals.get('country_id', False)
                    if rec.country_id:
                        message += rec.country_id.name +"&nbsp;-->&nbsp;"
                    else:
                        message += "None &nbsp;-->&nbsp;"
                
                    if country_id:
                        country = rec.env['res.country'].browse(country_id)
                        message += country.name + "&nbsp;(country)<br/>"
                    else:
                        message += "None &nbsp;(country)<br/>"

                if 'state_id' in vals_keys:
                    if rec.state_id:
                        message += rec.state_id.name +"&nbsp;-->&nbsp;"
                    else:
                        message +="None &nbsp;-->&nbsp;"

                    state_id = vals.get('state_id', False)
                    if state_id:
                        state = self.env['res.country.state'].browse(state_id)
                        message += state.name + "&nbsp;(state)<br/>"
                    else:
                        message += "None &nbsp;(state)<br/>"

            if message:
                message = Markup("Delivery Address changed <br/>" + message)
                sale_orders = so_obj.search([('partner_shipping_id', '=', rec.id)])
                if sale_orders:
                    for sale_order in sale_orders:
                        sale_order.message_post(body=message)

        res = super(SaleOrderExt, self).write(vals)
        return res