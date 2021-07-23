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

class vehicle_seats_compute(models.TransientModel):
    _name = 'vehicle.seats.compute'

    start_date = fields.Date('Start Date', default='2015-01-01')
    end_date = fields.Date('End Date',  default='2015-12-31')

    @api.multi
    def vehicle_report_call(self):
        if self.start_date > self.end_date:
            raise Warning(_('Start Date should not be greater then End Date'))

        vehicle_id = self._context['active_id']
        if vehicle_id:
            trip_obj = self.env['fleet.trip']
            trip_ids = trip_obj.search([('vehicle_id', '=', vehicle_id),('start_time', '>=',self.start_date),('start_time', '<=', self.end_date)])
            if trip_ids:
                data = self.read()[0]
                data.update({'vehicle_id': vehicle_id,})
                datas = {
                    'ids': self._ids,
                    'model': 'vehicle.seats.compute',
                    'form': data,
                }
                return  self.env['report'].get_action(self, 'spantree_logistics.vehicle_wise_booking_template',data=datas,)
            else:
                raise except_orm(_('Trip Not Found'), _("Vehicle is not use for any Trip between %s To %s" %(self.start_date, self.end_date)))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: