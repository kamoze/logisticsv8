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


class vehicle_wise_booking(models.AbstractModel):
    _name = 'report.spantree_logistics.vehicle_wise_booking_template'

    amount_total = 0.0
    total_expense = 0.0

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.vehicle_wise_booking_template')
        docargs = {
            'doc_ids': self.env["vehicle.seats.compute"].browse(data["ids"]),
            'doc_model': report.model,
            'docs': self,
            'get_vehicle_id': self._get_vehicle_id,
            'get_vehicle_name': self._get_vehicle_name,
            'get_total_amount': self._get_total_amount,
            'get_total_expense' : self._get_total_expense,
            'get_total_profit' : self._get_total_profit,
            'get_total_loose' : self._get_total_loose,
            'data': data,
        }
        return report_obj.render('spantree_logistics.vehicle_wise_booking_template', docargs)

    def _get_total_profit(self):
        total = 0.0
        if self.amount_total > self.total_expense:
            total = self.amount_total - self.total_expense
        return total

    def _get_total_loose(self):
        total = 0.0
        if self.amount_total < self.total_expense:
            total = self.total_expense - self.amount_total
        return total

    def _get_vehicle_name(self, vehicle_id):
        vehicle_name = self.env['fleet.vehicle'].search([('id', '=', vehicle_id)])
        return vehicle_name.name

    def _get_total_expense(self, vehicle_id):
        cost_obj = self.env['fleet.vehicle.cost']
        cost_ids = cost_obj.search([('vehicle_id', '=', vehicle_id)])
        if vehicle_id:
            for cost_id in cost_ids:
                self.total_expense += cost_id.amount
        return self.total_expense

    def _get_vehicle_id(self, vehicle_id, start_date, end_date):
        value = []
        trip_obj = self.env['fleet.trip']
        booking_obj = self.env['fleet.trip.reservation']
        trip_ids = trip_obj.search([('vehicle_id', '=', vehicle_id),('start_time', '>=',start_date),('start_time', '<=', end_date)])
        for trip_id in trip_ids:
            booking_ids = booking_obj.search(['|', ('trip_id', '=', trip_id.id), ('return_trip_id', '=', trip_id.id)])
            val = {}
            total_price = 0
            total_seat = 0
            for booking in booking_ids:
                if booking.state == 'confirmed':
                    for seat in booking.seat_ids:
                        total_price += seat.price
                        total_seat += 1
                if booking.return_trip_id:
                    total_price = total_price/2
                    total_seat = total_seat/2
            self.amount_total += total_price
            val.update({'trip_name': trip_id.name,
                    'total_price': total_price,
                    'total_seat': total_seat})
            value.append(val)
        return value

    def _get_total_amount(self):
        return self.amount_total

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: