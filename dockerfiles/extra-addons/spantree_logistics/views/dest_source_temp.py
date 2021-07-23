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


class report_dest_source_temp(models.AbstractModel):
    _name = 'report.spantree_logistics.report_dest_source_temp'

    @api.multi
    def render_html(self, data=None):
        qty = 0
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_dest_source_temp')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'get_lug_number' : self._get_lug_number,
        }
        trip_res = self.env['fleet.trip.reservation']
        record = trip_res.browse(self.id)
        if record.return_trip_id:
            for seat in record.seat_ids:
                if record.dest_id.id == seat.source_id.id and record.source_id.id == seat.dest_id.id:
                    qty = qty + seat.luggage_qty
            if qty <= 0:
                raise RedirectWarning(_('There are no luggages to Print...!'))
        else:
            raise RedirectWarning(_('Return Trip for this Trip is not Defined...!'))
        return report_obj.render('spantree_logistics.report_dest_source_temp', docargs)

    def _get_lug_number(self, data):
        value = []
        for seat in data.seat_ids:
            if data.dest_id.id == seat.source_id.id and data.source_id.id == seat.dest_id.id:
                for qty in range(1,seat.luggage_qty+1):
                    val = {}
                    barcode = data.return_trip_id.name+'/'+str(seat.seat_no.seat_no)+'/'+str(qty)
                    val.update({'customer_name' : seat.name, 'trip_name': seat.trip_id.name,
                                'seat_number': seat.seat_no.id, 'luggage_number' : qty,
                                'b_name':barcode})
                    value.append(val)
        if value:
            return value
        else:
            raise Exception("There is no luggage")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: