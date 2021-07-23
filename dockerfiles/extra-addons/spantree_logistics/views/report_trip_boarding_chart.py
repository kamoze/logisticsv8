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


class report_trip_boarding_chart_temp(models.AbstractModel):
    _name = 'report.spantree_logistics.report_trip_boarding_chart_temp'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_trip_boarding_chart_temp')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'get_board_passenger_list': self._get_board_passenger_list,
            'get_date':self._get_date,
            'get_total': self._get_total
        }
        return report_obj.render('spantree_logistics.report_trip_boarding_chart_temp', docargs)

    def _get_board_passenger_list(self, data):
        passenger_list = []
        pass_list = data.reservation_seat_ids
        for pass_detail in pass_list:
            passenger_list.append({'partner_id': pass_detail.partner_id.name,
                                   'kin_name': pass_detail.partner_id and pass_detail.partner_id.kin_name and pass_detail.partner_id.kin_name or False,
                                   'kin_no': pass_detail.partner_id and pass_detail.partner_id.kin_no and pass_detail.partner_id.kin_no or False,
                                   'passenger_type':pass_detail.passenger_type.name,
                                   'source_id': pass_detail.source_id.name,
                                   'dest_id': pass_detail.dest_id.name,
                                   'board_loc_id': pass_detail.board_loc_id.name,
                                   'trip_id': pass_detail.trip_id.name,
                                   'seat_no': pass_detail.seat_no.id,
                                   'price': pass_detail.price,
                                   'is_board': pass_detail.is_board})
        sorted_passenger_list = sorted(passenger_list, key=lambda k: int(k['seat_no']))
        return sorted_passenger_list

    def _get_total(self, data):
        total = 0.0
        for line in data.reservation_seat_ids:
            total = total + float(line.price)
        return total

    def _get_date(self):
         return date.today()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: