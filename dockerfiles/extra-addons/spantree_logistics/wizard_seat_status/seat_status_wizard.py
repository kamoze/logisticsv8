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
#############################################################################
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import fields, models, api, _
import datetime
import time
from datetime import date
from dateutil.relativedelta import relativedelta

class seat_status_wizard(models.TransientModel):
    _name = 'seat.status.wizard'

    date = fields.Date('Date')
    trip_id = fields.Many2one('fleet.trip', "Trip", required = True)
    route_id = fields.Many2one('fleet.route', 'Route')

    @api.multi
    def get_data(self):
        fleet_trip_ids = self.env['fleet.trip'].search([])
        return self.env['report'].get_action(self.trip_id[0], 'spantree_logistics.report_seat_reservation_temp')

    @api.onchange("date","route_id")
    @api.multi
    def onchange_fill_trip_date(self):
        if self.date and not self.route_id:
            date_conv = datetime.datetime.strptime(self.date, '%Y-%m-%d')
            start_date = datetime.datetime.strftime(date_conv, '%Y-%m-%d 0:0:0')
            end_date = datetime.datetime.strftime(date_conv, '%Y-%m-%d 23:59:59')
            trip_ids = self.env['fleet.trip'].search([('start_time',">=",start_date),('start_time',"<=",end_date)])
            trip_ids_in_list = [x.id for x in trip_ids]
            return {'domain':{'trip_id':[('id','in',trip_ids_in_list)]}}
        elif not self.date and self.route_id:
            trip_ids = self.env['fleet.trip'].search([('route_id.id',"=",self.route_id.id)])
            trip_ids_in_list = [x.id for x in trip_ids]
            return {'domain':{'trip_id':[('id','in',trip_ids_in_list)]}}
        elif not self.date and not self.route_id:
            return {}
        else:
            date_conv = datetime.datetime.strptime(self.date, '%Y-%m-%d')
            start_date = datetime.datetime.strftime(date_conv, '%Y-%m-%d 0:0:0')
            end_date = datetime.datetime.strftime(date_conv, '%Y-%m-%d 23:59:59')
            trip_ids = self.env['fleet.trip'].search([('start_time',">=",start_date),('start_time',"<=",end_date),('route_id.id',"=",self.route_id.id)])
            trip_ids_in_list = [x.id for x in trip_ids]
            return {'domain':{'trip_id':[('id','in',trip_ids_in_list)]}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: