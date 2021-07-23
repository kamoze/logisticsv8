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
from datetime import datetime, date, time, timedelta
from openerp.exceptions import except_orm, Warning, RedirectWarning


class ticket_report_methods(models.AbstractModel):
    _name = 'report.spantree_logistics.report_ticket_temp'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_ticket_temp')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'get_time':self._get_time,
            'get_date':self._get_date,
            'get_trip_seat':self._get_trip_seat,
            'get_return_trip_seat' : self._get_return_trip_seat,
            'get_validation_date' : self._get_validation_date,
            'get_return_trip_seat_empty' : self._get_return_trip_seat_empty,
        }
        trip_res = self.env['fleet.trip.reservation']
        record = trip_res.browse(self.id)
        if not record.seat_ids:
            raise RedirectWarning(_('Please, Reserve the seats first...!'))
        return report_obj.sudo().render('spantree_logistics.report_ticket_temp', docargs)

    def _get_validation_date(self, trip_date):
        if trip_date:
            trip_date = datetime.strptime(trip_date, '%Y-%m-%d') + timedelta(days=30)
            trip_date = datetime.strftime(trip_date, '%d/%m/%Y')
            return trip_date

    def _get_trip_seat(self, res):
        seats = res.seat_ids.filtered(lambda record: record.source_id.id == res.source_id.id) and res.seat_ids.filtered(lambda record: record.dest_id.id == res.dest_id.id)
        return seats

    def _get_return_trip_seat(self, res):
        seats = False
        if res.return_trip:
            if res.return_trip_id:
                seats = res.seat_ids.filtered(lambda record: record.source_id.id == res.dest_id.id) and res.seat_ids.filtered(lambda record: record.dest_id.id == res.source_id.id)
        return seats

    def _get_return_trip_seat_empty(self, res):
        seats = []
        if res.return_trip and not res.return_trip_id:
            for seat in res.seat_ids:
                seat_dict = {}
                seat_dict.update({'passenger_name' : seat.name, 'price' : 0.0})
                seats.append(seat_dict)
        return seats


    def _get_time(self,date_dept):
        b_time = (datetime.strptime(date_dept,"%Y-%m-%d %H:%M:%S").time())
        return b_time

    def _get_date(self,date_dept):
        b_date = (datetime.strptime(date_dept,"%Y-%m-%d %H:%M:%S").date())
        return b_date

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: