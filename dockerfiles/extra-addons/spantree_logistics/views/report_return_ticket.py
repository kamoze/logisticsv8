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
from datetime import datetime, date, time
from openerp.exceptions import except_orm, Warning, RedirectWarning


class ticket_return_report_methods(models.AbstractModel):
    _name = 'report.spantree_logistics.report_return_ticket_temp'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_return_ticket_temp')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'get_time':self._get_time,
            'get_date':self._get_date,
            'get_trip_seat':self._get_trip_seat,
#             'get_fare':self.fare,    
        }
        trip_res = self.env['fleet.trip.reservation']
        record = trip_res.browse(self.id)
        if not record.seat_ids:
            raise RedirectWarning(_('Please, Reserve the seats first...!'))
        return report_obj.render('spantree_logistics.report_return_ticket_temp', docargs)
    
    def _get_trip_seat(self,res):
        seats = res.seat_ids.filtered(lambda record: record.dest_id.id == res.source_id.id) and res.seat_ids.filtered(lambda record: record.source_id.id == res.dest_id.id)
        return seats

    def _get_time(self,date_dept):
        b_time = (datetime.strptime(date_dept,"%Y-%m-%d %H:%M:%S").time())
        return b_time

    def _get_date(self,date_dept):
        b_date = (datetime.strptime(date_dept,"%Y-%m-%d %H:%M:%S").date())
        return b_date

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: