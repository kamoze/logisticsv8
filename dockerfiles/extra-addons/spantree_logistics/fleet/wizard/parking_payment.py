# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013-Present Acespritech Solutions Pvt. Ltd. (<http://acespritech.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime, timedelta, date, time
import math
from pytz import timezone


class parking_payment(models.TransientModel):
    _name = "parking.payment"

    create_invoice = fields.Boolean('To Be Invoiced', default=True)
    fixed_charge = fields.Boolean('Fixed Charge', default=True)
    type_charge = fields.Selection([('hour', 'Hours'), ('daily', 'Daily'), ('week', 'Week')], 
                                   string='Charges Based On', default="daily")
    end_time = fields.Datetime('End Time')
    hours = fields.Float(string="Hours")
    weeks = fields.Integer(string="Weeks")

    @api.one
    def _create_move(self, parking_brw,):
        # create Incoming Move for the vehicle
        move_default = self.env['stock.move'].default_get(['invoice_state', 'priority', 'date_expected', 'partner_id', 'procure_method',
                                                           'picking_type_id', 'company_id', 'reserved_quant_ids', 'product_uom'])
        source_loc_id = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_customers')[1]
        dest_loc_id = parking_brw.park_location_id.location_id.id
        move_prod_onchange = self.env['stock.move'].onchange_product_id(prod_id=parking_brw.type_id.product_id.id, loc_id=source_loc_id, loc_dest_id=dest_loc_id)
        move_data = {'parking_id': parking_brw.id, 'product_id':parking_brw.type_id.product_id.id}
        move_data.update(move_default)
        move_data.update(move_prod_onchange.get('value'))
        move_brw = self.env['stock.move'].create(move_data)
        if move_brw:
            move_brw.action_done()
            parking_brw.state = 'parked'
        return True

    @api.one
    def _finalize_fixed(self, parking_id, fixed_amt):
        # Method to run when we ant to create
        parking_brw = self.env['fleet.parking'].browse(parking_id)
        parking_brw.charge = parking_brw.type_id.fixed_price
        parking_brw.total_charge = parking_brw.type_id.fixed_price
        parking_brw.to_be_invoiced = True
        return parking_brw.type_id.fixed_price

    @api.one
    def _finalize_days(self, parking_id):
        parking_brw = self.env['fleet.parking'].browse(parking_id)
        start_time = datetime.strptime(parking_brw.start_time, '%Y-%m-%d %H:%M:%S')
        if self.type_charge == 'daily':
            parking_brw.charge = parking_brw.type_id.charge_price
            end_time = datetime.strptime(self.end_time, '%Y-%m-%d %H:%M:%S')
            parking_brw.end_time = end_time
            parking_brw.no_of_days = (end_time - start_time).days
            parking_brw.total_charge = parking_brw.charge * parking_brw.no_of_days
        elif self.type_charge == 'hour':
            parking_brw.charge = parking_brw.type_id.hour_price
            hour = math.floor(self.hours)
            minite = round((self.hours % 1) * 60)
            if minite == 60:
                minite = 0
                hour = hour + 1
            hour = str(hour).split(".")
            minite = str(minite).split(".")
            end_time = datetime.strptime(parking_brw.start_time, '%Y-%m-%d %H:%M:%S') + timedelta(hours=int(hour[0]), minutes=int(minite[0]))
            parking_brw.no_of_days = (end_time - start_time).days
            parking_brw.end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
            parking_brw.total_charge = parking_brw.charge * self.hours
        elif self.type_charge == 'week':
            no_of_days = self.weeks*7
            parking_brw.charge = parking_brw.type_id.weekly_price
            end_time = datetime.strptime(parking_brw.start_time, '%Y-%m-%d %H:%M:%S') + timedelta(days=no_of_days)
            parking_brw.no_of_days = (end_time - start_time).days
            parking_brw.end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
            parking_brw.total_charge = parking_brw.charge * self.weeks
        parking_brw.to_be_invoiced = True
        parking_brw.charge_type = self.type_charge
        return parking_brw.total_charge

    @api.one
    def finalize(self):
        if not self.fixed_charge and not self.type_charge:
            raise Warning(_('Select any charge type to finalize the parking price.'))
        create_inv = self.create_invoice
        fixed_charge = self.fixed_charge
        final_amt = 0.0
        if self._context.get('active_id'):
            parking_brw = self.env['fleet.parking'].browse(self._context.get('active_id'))
            if not create_inv:
                if fixed_charge:
                    parking_brw.charge = parking_brw.type_id.fixed_price
                    parking_brw.total_charge = parking_brw.type_id.fixed_price
                    parking_brw.charge_type = 'fixed'
                else:
                    parking_brw.end_time = self.end_time
                    parking_brw.charge = parking_brw.type_id.charge_price
            if create_inv:
                if fixed_charge:
                    final_amt = self._finalize_fixed(parking_brw.id, parking_brw.type_id.fixed_price)
                    parking_brw.charge_type = 'fixed'
                else:
                    final_amt = self._finalize_days(parking_brw.id)
                # create Invoice
            self._create_move(parking_brw)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: