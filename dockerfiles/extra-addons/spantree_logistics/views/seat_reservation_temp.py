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

from openerp import api, models
from datetime import datetime, date, time


class report_seat_reservation_temp(models.AbstractModel):
    _name = 'report.spantree_logistics.report_seat_reservation_temp'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_seat_reservation_temp')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'stat_seats_reserved': self._stat_seats_reserved,
            'get_date':self._get_date,
        }
        return report_obj.render('spantree_logistics.report_seat_reservation_temp', docargs)

    def _stat_seats_reserved(self, data):
        trip_res = self.env['fleet.trip.reservation']
        trip_id = data.route_id
        seats_data = trip_res.find_routewise_seats(trip_id.city_source.id, trip_id.city_destination.id, data.id)
        seat_ids = []
        for r in trip_res.browse(seats_data.get('clashed_trip_res_ids', [])):
            for seat_line in r.seat_ids:
                if seat_line.trip_id.id == data.id:
                    seat_ids.append({
                                'seat_no': seat_line.seat_no.seat_no,
                                'passenger_name': seat_line.name,
                                'boarding_location' : seat_line.board_loc_id.name,
                                'city_destination': seat_line.dest_id.name,
                                'passenger_type':seat_line.passenger_type.name,
                            })
        sorted_seat_ids = sorted(seat_ids, key=lambda k: k['seat_no'])
        return sorted_seat_ids

    def _get_date(self):
         return date.today()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: