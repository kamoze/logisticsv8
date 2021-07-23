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


class report_trip_boarding_luggage_temp(models.AbstractModel):
    _name = 'report.spantree_logistics.report_trip_boarding_luggage_temp'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_trip_boarding_luggage_temp')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'get_board_pass_luggage_list': self._get_board_pass_luggage_list,
            'get_date':self._get_date,
        }
        return report_obj.render('spantree_logistics.report_trip_boarding_luggage_temp', docargs)

    def _get_board_pass_luggage_list(self, data):
        passenger_luggage_list = []
        luggage_list = data.luggage_ids
        for each_luggage_detail in luggage_list:
            passenger_luggage_list.append({'trip_name': each_luggage_detail.trip_id.name,
                                           'pass_name': each_luggage_detail.passenger_id.name,
                                           'luggage_detail': each_luggage_detail.luggage_name,
                                           'source_id': each_luggage_detail.source_id.name,
                                           'dest_id': each_luggage_detail.destination_id.name,
                                           'charge': each_luggage_detail.charge,
                                           'weight': each_luggage_detail.weight,
                                           'rate': each_luggage_detail.rate,
                                           'total': each_luggage_detail.total})
        sorted_pass_luggage_list = sorted(passenger_luggage_list, key=lambda k: k['pass_name'])
        return sorted_pass_luggage_list

    def _get_date(self):
         return date.today()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: