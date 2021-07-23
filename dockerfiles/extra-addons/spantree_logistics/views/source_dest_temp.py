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

class report_source_dest_temp(models.AbstractModel):
    _name = 'report.spantree_logistics.report_source_dest_temp'

    @api.multi
    def render_html(self, data=None):
        qty = 0
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_source_dest_temp')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'get_lug_number' : self._get_lug_number,
        }
        trip_res = self.env['fleet.trip.reservation']
        record = trip_res.browse(self.id)
        for each_luggage in record.luggage_ids:
            if record.source_id.id == each_luggage.source_id.id and record.dest_id.id == each_luggage.destination_id.id:
                qty = qty + 1
        if qty <= 0:
            raise RedirectWarning(_('There are no luggages to Print...!'))
        return report_obj.render('spantree_logistics.report_source_dest_temp', docargs)

    def _get_lug_number(self, data):
        value = []
        for each_luggage in data.luggage_ids:
            if data.source_id.id == each_luggage.source_id.id and data.dest_id.id == each_luggage.destination_id.id:
                if each_luggage.seat_id:
                    val = {}
                    barcode = self.env['trip.reservation.seat'].search([('reservation_id', '=', each_luggage.reservation_id.id),
                                                                        ('trip_id', '=', each_luggage.trip_id.id),
                                                                        ('seat_no', '=', each_luggage.seat_id.id)])
                    if barcode:
                        val.update({'customer_name' : each_luggage.passenger_id.name,
                                    'trip_name': each_luggage.trip_id.name,
                                    'seat_number': each_luggage.seat_id.id,
                                    'luggage_name' : each_luggage.luggage_name,
                                    'b_name':barcode,
                                    'vehicle': each_luggage.trip_id.vehicle_id and each_luggage.trip_id.vehicle_id.name})
                        value.append(val)
                        value.append(val)
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: