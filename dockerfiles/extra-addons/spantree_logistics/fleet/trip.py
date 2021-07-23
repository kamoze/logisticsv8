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

from openerp import models, fields, api, _, netsvc
from datetime import datetime, timedelta, date
import time
from lxml import etree
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
wf_service = netsvc.LocalService("workflow")
from openerp import SUPERUSER_ID
from openerp.osv.orm import setup_modifiers
from pytz import timezone
import textwrap

class res_company(models.Model):
    _inherit = "res.company"

    phone2 = fields.Char(string="Phone 2")
#     server_id = fields.Integer('Server ID')
# 
#     @api.model
#     def create(self, vals):
#         if self._uid != SUPERUSER_ID:
#             raise except_orm(_('You can not create this record'),
#                             ('please contact to admin to create a record'))
#         return super(res_country, self).create(vals)
# 
#     @api.one
#     def write(self, vals):
#         if self._uid != SUPERUSER_ID:
#             raise except_orm(_('You can not write this record'),
#                             ('please contact to admin to write a record'))
#         return super(res_country, self).write(vals)
# 
#     @api.multi
#     def unlink(self):
#         if self._uid != SUPERUSER_ID:
#             raise except_orm(_('You can not delete this record'),
#                             ('please contact to admin to delete a record'))
#         return super(res_country, self).unlink()


class fleet_trip_reservation(models.Model):
    _name = 'fleet.trip.reservation'

    def get_tickets(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        document = self.browse(cr, uid, ids[0], context=context)
        tickets_no = []
        for seat_id in document.seat_ids:
            if seat_id.trip_id.id == document.trip_id.id:
                tickets_no.append(seat_id.seat_no.id)
        return tickets_no

    def get_return_tickets(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        document = self.browse(cr, uid, ids[0], context=context)
        tickets_no = []
        if document.return_trip and document.return_trip_id:
            for seat_id in document.seat_ids:
                if seat_id.trip_id.id == document.return_trip_id.id:
                    tickets_no.append(seat_id.seat_no.id)
            return tickets_no

    @api.multi
    def view_invoice(self):
        if self.invoice_id:
            view_id = self.env['ir.model.data'].get_object_reference('account', 'invoice_form')[1]
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'view_id': [view_id],
                'res_id': self.invoice_id.id or False,
                'type': 'ir.actions.act_window',
            }

    @api.multi
    def print_tickets(self):
        """ Print tickets when the tickets are """
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        self.sent = True
        return self.env['report'].get_action(self, 'spantree_logistics.report_ticket_temp')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res_user_brw = self.env['res.users'].browse(self._uid)
        result = super(fleet_trip_reservation, self).fields_view_get(view_id=view_id, view_type=view_type,
                                           toolbar=toolbar, submenu=False)
        if view_type in ['tree', 'form']:
            for elm in result.get('toolbar').get('print'):
                if elm.get('string') == "Tickets":
                    result['toolbar']['print'].remove(elm)
            if self._uid == SUPERUSER_ID or self.pool['res.users'].has_group(self._cr, self._uid, 'spantree_logistics.group_cashier_user'):
                doc = etree.XML(result['arch'])
                for node in doc.xpath("//button[@name='make_payment']"):
                    node.set('confirm', 'Are you sure you want to make payment for this trip?')
                    result['arch'] = etree.tostring(doc)
#                 result['arch'] = etree.tostring(doc)
        return result

    @api.model
    def find_routewise_seats(self, scity, dcity, trip):
        """
        scity = id source city fleet.city
        dcity = id of dest. city fleet.city
        trip = id of trip,  fleet.trip
        return eg: dict {'used_seats': [2,5,8],'free_seats': [10],'clashed_trip_res_ids':[1,4,6,8] }
        """
        city_env = self.env['fleet.city']
        scity = city_env.browse(scity)
        dcity = city_env.browse(dcity)
        trip = self.env['fleet.trip'].browse(trip)
        route = trip.route_id
        route_cities, used_seats, free_seats, total_seats, clashed_res = [], [], [], [], []
        clashed_trip_trs = []
        route_cities.append(route.city_source.id)
        # add point cities based on sequence
        route_points = self.env['fleet.route.point'].search([('route_id', '=', route.id)], order='sequence_no ASC')
        if route_points:
            for each_point in route_points:
                route_cities.append(each_point.city_id.id)
        route_cities.append(route.city_destination.id)
        # prepare for finding if trip_res clash or not
        all_trip_ftr = []

        all_trs = self.env['trip.reservation.seat'].search([('trip_id', '=', trip.id)])
        for es in all_trs:
            if es.reservation_id.state == 'confirmed':
                all_trip_ftr.append(es.reservation_id)
        all_trip_ftr = list(set(all_trip_ftr))

        # all_trs has br of all trip_seats having same trip
        for each_res in all_trip_ftr:
            for each_res_seat in each_res.seat_ids:
                if each_res_seat.source_id.id in route_cities[:route_cities.index(scity.id) + 1] and each_res_seat.dest_id.id in route_cities[route_cities.index(scity.id) + 1: ]:
                    clashed_trip_trs.append(each_res_seat)
                elif each_res_seat.source_id.id in route_cities[route_cities.index(scity.id):route_cities.index(dcity.id)]:
                    clashed_trip_trs.append(each_res_seat)

        clashed_all_trip_ftr = []
        for etrs in clashed_trip_trs:
            if etrs.reservation_id not in clashed_all_trip_ftr:
                clashed_all_trip_ftr.append(etrs.reservation_id)
        # now find seats occupied by the clashed_trip_trs:
        used_seats = [x.seat_no.id for x in clashed_trip_trs if x.trip_id.id == trip.id]
#         if self._context.get('active_model') and self._context.get('active_id') \
#            and self._context['active_model'] == 'fleet.trip.reservation':
        if self._context.get('active_ids'):
            trip_id = False
            if self._context.get('active_model') and self._context.get('active_model') == 'account.invoice':
                trip_res = self.search([('invoice_id', '=', self._context['active_ids'][0])])
            else:
                trip_id = self._context.get('active_ids')
            if trip_id:
                trip_res = self.browse(trip_id)
            used_seats += [x.seat_no.id for x in trip_res.seat_ids if x.trip_id.id == trip.id]
        # now find free seats--------
        if trip and trip.vehicle_id and trip.vehicle_id.seat_active:
            all_seats = [x.id for x in trip.vehicle_id.seat_nos]
        else:
            config = self.env['config.setting.transport'].search([])
            if config:
                config_seat_amt = config[-1].seat_nos
            else:
                model, action_id = self.env['ir.model.data'].get_object_reference('spantree_logistics', 'action_config_transport')
                msg = _("You have not set Seat Numbers in the Configuration Panel .\n To set default seat numbers, please go to Misellaneous Settings.")
                raise RedirectWarning(msg, action_id, _('Go to the configuration panel'))
            all_seats = self.env['fleet.vehicle.seat'].search([('vehicle_id', '=', False), ('seat_no', 'in', [str(x) for x in range(1, config_seat_amt + 1)])])
            all_seats = [x.id for x in all_seats]
        free_seats = [x for x in all_seats if x not in used_seats]
        res = {'used_seats': used_seats, 'free_seats': free_seats, 'clashed_trip_res_ids': [x.id for x in clashed_all_trip_ftr]}
        return res

    @api.multi
    def write(self, vals):
        '''if seats are confirm and trip or return trip get change values into
        seat line also get change'''
        if self._context.get('from_cloud'):
            return super(fleet_trip_reservation, self).write(vals)
        else:
            trip_res_obj = self.env['trip.reservation.seat']
            current_date = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
            current_date = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
            '''update existing trip line records for regular trip'''
            # check if trip date is greater then return trip
            return_date = vals.get('return_date') or self.return_date or False
            trip_date = vals.get('trip_date') or self.trip_date or False
            if return_date and trip_date and self.return_trip:
                if datetime.strptime(trip_date, '%Y-%m-%d') > \
                    datetime.strptime(return_date, '%Y-%m-%d'):
                    raise RedirectWarning(_('Return Trip date should be greater then Trip Date..!'))
            # check if trip date is greater then today or date does not match to trip date
            if vals.get('trip_date') and not vals.get('trip_id'):
                if (date.today() > datetime.strptime(vals.get('trip_date'), '%Y-%m-%d').date()):
                    raise RedirectWarning(_('Trip Date should be greater then Today..!'))
                if current_date >= datetime.strptime(self.trip_id.start_time, '%Y-%m-%d %H:%M:%S'):
                    if datetime.strptime(self.trip_date, '%Y-%m-%d') <= \
                        datetime.strptime(vals.get('trip_date'), '%Y-%m-%d'):
                        raise RedirectWarning(_('Trip Date mis-match into Ticket...!, You might have changed the date of trip which is already occurred.'))
            # check if trip change count new trip seats and update trip lines in ticket
            if vals.get('trip_id'):
                seats_data = self.find_routewise_seats(self.source_id.id, self.dest_id.id, vals.get('trip_id'))
                if not seats_data.get('free_seats'):
                    raise Warning(_('Oops !, No Seats Left'))
                trip_seats = []
                for seat in self.seat_ids:
                    if (self.source_id.id == seat.source_id.id) and (self.dest_id.id == seat.dest_id.id):
                        trip_seats.append(seat.id)
                if len(seats_data.get('free_seats')) < len(trip_seats):
                    raise except_orm(_('Not Enough Tickets'), _('Oops !, Only %d Seats Left in this Trip') \
                         % (len(seats_data.get('free_seats'))))
                seat_no = 0
                for seat in self.seat_ids:
                    if (self.source_id.id == seat.source_id.id) and (self.dest_id.id == seat.dest_id.id):
                        if seat.trip_id.id != vals.get('trip_id'):
                            seat.write({'trip_id' : vals.get('trip_id'), 'seat_no' : seats_data.get('free_seats')[seat_no]})
                            seat_no += 1
            # check if trip date is greater then 30 days give error on change of return trip
            if self.return_trip and vals.get('return_date'):
                if self.state == 'confirmed':
                    if self.return_trip_id:
                        if current_date > datetime.strptime(self.return_trip_id.start_time, '%Y-%m-%d %H:%M:%S'):
                            raise RedirectWarning(_('Return Trip Date mis-match into Ticket...!,You might have changed the date of Return trip which is already occurred'))
                    trip_date = vals.get('trip_date') if vals.get('trip_date') else self.trip_date
                    if (date.today() - datetime.strptime(trip_date, '%Y-%m-%d').date()).days > 30:
                        raise RedirectWarning(_('Return Trip Date mis-match into Ticket...!,You might have changed the date of Return trip which is already expired.'))
            # if retunr trip
            if vals.get('return_trip_id'):
                mega_list_return = []
                seats_data = self.find_routewise_seats(self.dest_id.id, self.source_id.id, vals.get('return_trip_id'))
                if not seats_data.get('free_seats'):
                    raise Warning(_('Oops !, No Seats Left'))
                return_trip_seat = []
                for seat in self.seat_ids:
                    if (self.source_id.id == seat.dest_id.id) and (self.dest_id.id == seat.source_id.id):
                        return_trip_seat.append(seat.ids)
                if len(seats_data.get('free_seats')) < len(return_trip_seat):
                    raise except_orm(_('Not Enough Tickets'), _('Oops !, Only %d Seats Left in this Trip') \
                         % (len(seats_data.get('free_seats'))))
                '''if return trip is not exists then 
                create new return trip line'''
                if not self.return_trip_id:
                    seat_no = 0
                    for seat in self.seat_ids:
                        mega_list_return.append({'passenger_type': seat.passenger_type.id,
                                                  'seat_qty': 1,
                                                  'price': 0.0,  # price gets filled by compute fields
                                                  'seat_no': seats_data.get('free_seats')[seat_no],
                                                  'reservation_id': self.id,
                                                  'trip_id': vals.get('return_trip_id'),
                                                  'source_id': self.dest_id.id,
                                                  'dest_id': self.source_id.id,
                                                  'name': self.customer_id.name,
                                                  'board_loc_id' : vals.get('return_park_loc_id') if vals.get('return_park_loc_id') else self.return_park_loc_id.id,
                                                 })
                        seat_no += 1
                    for line in mega_list_return:
                        trip_res_obj.create(line)
                else:
                    '''Update the Existing line for return Trip'''
                    seat_no = 0
                    for seat in self.seat_ids:
                        if (self.source_id.id == seat.dest_id.id) and (self.dest_id.id == seat.source_id.id):
                            if seat.trip_id.id != vals.get('return_trip_id'):
                                seat.write({'trip_id' : vals.get('return_trip_id'), 'seat_no' : seats_data.get('free_seats')[seat_no]})
                                seat_no += 1
            return super(fleet_trip_reservation, self).write(vals)

    @api.multi
    def onchange_fill_trip_date(self, trip_id):
        '''fill the date of trip on change of trip value'''
        if trip_id:
            trip_data = self.env['fleet.trip'].search([('id', '=', trip_id)])
            return {'value': {'trip_date': trip_data.start_time or False}}
        return {}

    @api.multi
    def onchange_fill_return_trip_date(self, return_trip_id):
        '''fill the return date of trip on change of return trip'''
        if return_trip_id:
            trip_data = self.env['fleet.trip'].search([('id', '=', return_trip_id)])
            return {'value':{'return_date':trip_data.start_time or False}}
        return {}

    @api.multi
    def onchange_fill_trip(self, source_id, dest_id, trip_date, trip_id):
        # This Method fills the trip_id based on date, source and dest city
        # TODO: add the missing context parameter when forward-porting in trunk
        # so we can remove this hack!
        '''to fill return parking location'''
        parking_obj = self.env['fleet.parking.location']
        park_ids = []
        default_location = []
        if source_id:
            park_ids = [x.id for x in parking_obj.search([('city_id', '=', source_id)])]
            default_location = [x.id for x in parking_obj.search([('city_id', '=', source_id), ('default_location', '=', True)], limit=1)]
        else:
            park_ids = [x.id for x in parking_obj.search([])]
        # check if state in confirmed and trip date is less then today date
        trip_obj = self.env['fleet.trip']
        trip_data = trip_obj.search([('id', '=', trip_id)])
        trip_ids = trip_obj.search([])
        current_date = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        current_date = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
        final_trips = []
        if trip_date:
            if (date.today() > datetime.strptime(trip_date, '%Y-%m-%d').date()):
                raise RedirectWarning(_('Trip Date should be greater then Today..!'))
        if self.state == 'confirmed':
            if current_date and self.trip_id.start_time and (current_date >= datetime.strptime(self.trip_id.start_time, '%Y-%m-%d %H:%M:%S')):
                if datetime.strptime(self.trip_id.start_time, '%Y-%m-%d %H:%M:%S') <= \
                    datetime.strptime(trip_data.start_time, '%Y-%m-%d %H:%M:%S'):
                    raise RedirectWarning(_('Trip can not change which is already occurred...!'))
        if source_id and dest_id and trip_date:
            for each_trip in trip_ids:
                if each_trip.start_time:
                    each_trip_date = datetime.strptime(
                        each_trip.start_time, '%Y-%m-%d %H:%M:%S').date()
                    res_date = datetime.strptime(trip_date, '%Y-%m-%d').date()
                    if each_trip_date == res_date:
                        # for source_id match
                        city_seq = {}
                        [city_seq.update({x.city_id.id: x.sequence_no})
                         for x in each_trip.route_id.route_point_ids]
                        trip_source = each_trip.route_id.city_source.id
                        trip_dest = each_trip.route_id.city_destination.id
                        if source_id == trip_source and dest_id == trip_dest:
                            final_trips.append(each_trip.id)
                        elif source_id == trip_source and dest_id in city_seq.keys():
                            final_trips.append(each_trip.id)
                        elif source_id in city_seq.keys() and dest_id in city_seq.keys():
                            if city_seq[source_id] < city_seq[dest_id]:
                                final_trips.append(each_trip.id)
                        elif source_id in city_seq.keys() and dest_id == trip_dest:
                            final_trips.append(each_trip.id)
        elif source_id and dest_id:
            for each_trip in trip_ids:
                # for source_id match
                city_seq = {}
                [city_seq.update({x.city_id.id: x.sequence_no})
                 for x in each_trip.route_id.route_point_ids]
                # creating dict for city_id:seq_no pairs for the trip
                trip_source = each_trip.route_id.city_source.id
                trip_dest = each_trip.route_id.city_destination.id
                if source_id == trip_source and dest_id == trip_dest:
                    final_trips.append(each_trip.id)
                elif source_id == trip_source and dest_id in city_seq.keys():
                    final_trips.append(each_trip.id)
                elif source_id in city_seq.keys() and dest_id in city_seq.keys():
                    if city_seq[source_id] < city_seq[dest_id]:
                        final_trips.append(each_trip.id)
                elif source_id in city_seq.keys() and dest_id == trip_dest:
                    final_trips.append(each_trip.id)
        # Remove Old Trips
        for et in trip_obj.browse(final_trips):
            if datetime.strptime(et.start_time, '%Y-%m-%d %H:%M:%S') < datetime.today():
                try:
                    final_trips.pop(final_trips.index(et.id))
                except:
                    pass
        # Remove Old Trips
        return {'domain': {'trip_id': [('id', 'in', final_trips)], 'parking_loc_id': [('id', 'in', park_ids)]}, \
                'value': {'trip_id': final_trips and final_trips[0] or False, 'parking_loc_id': default_location and default_location[0] or False}}

    @api.multi
    def onchange_fill_return_trip(self, dest_id, source_id, return_date, trip_date, return_trip):
        # This Method fills the trip_id based on date, source and dest city
        # TODO: add the missing context parameter when forward-porting in trunk
        # so we can remove this hack!
        '''to fill return parking location'''
        parking_obj = self.env['fleet.parking.location']
        return_park_ids = []
        default_location = []
        current_date = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        current_date = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
        if return_trip and source_id:
            return_park_ids = [x.id for x in parking_obj.search([('city_id', '=', source_id)])]
            default_location = [x.id for x in parking_obj.search([('city_id', '=', source_id), ('default_location', '=', True)], limit=1)]
        else:
            return_park_ids = [x.id for x in parking_obj.search([])]
        # check if state in confirmed and trip date is less then today date
        trip_obj = self.env['fleet.trip']
        trip_ids = trip_obj.search([])
        final_trips = []
        if return_date:
            if (date.today() > datetime.strptime(return_date, '%Y-%m-%d').date()):
                raise RedirectWarning(_('Return Trip date should be greater then Today..!'))
            if self.state == 'confirmed':
                if self.return_trip_id:
                    if current_date > datetime.strptime(self.return_trip_id.start_time, '%Y-%m-%d %H:%M:%S'):
                        raise RedirectWarning(_('Return Trip can not change which is already occurred...!'))
                if (date.today() - datetime.strptime(self.trip_date, '%Y-%m-%d').date()).days > 30:
                    raise RedirectWarning(_('Return Trip Booking Time Expired...!'))
        # check if today date is less then trip date
        if source_id and dest_id and return_date:
            for each_trip in trip_ids:
                if each_trip.start_time:
                    each_trip_date = datetime.strptime(
                        each_trip.start_time, '%Y-%m-%d %H:%M:%S').date()
                    res_date = datetime.strptime(return_date, '%Y-%m-%d').date()
                    if each_trip_date == res_date:
                        # for source_id match
                        city_seq = {}
                        [city_seq.update({x.city_id.id: x.sequence_no})
                         for x in each_trip.route_id.route_point_ids]
                        trip_source = each_trip.route_id.city_source.id
                        trip_dest = each_trip.route_id.city_destination.id
                        if source_id == trip_source and dest_id == trip_dest:
                            final_trips.append(each_trip.id)
                        elif source_id == trip_source and dest_id in city_seq.keys():
                            final_trips.append(each_trip.id)
                        elif source_id in city_seq.keys() and dest_id in city_seq.keys():
                            if city_seq[source_id] < city_seq[dest_id]:
                                final_trips.append(each_trip.id)
                        elif source_id in city_seq.keys() and dest_id == trip_dest:
                            final_trips.append(each_trip.id)
        elif source_id and dest_id:
            for each_trip in trip_ids:
                # for source_id match
                city_seq = {}
                [city_seq.update({x.city_id.id: x.sequence_no})
                 for x in each_trip.route_id.route_point_ids]
                # creating dict for city_id:seq_no pairs for the trip
                trip_source = each_trip.route_id.city_source.id
                trip_dest = each_trip.route_id.city_destination.id
                if source_id == trip_source and dest_id == trip_dest:
                    final_trips.append(each_trip.id)
                elif source_id == trip_source and dest_id in city_seq.keys():
                    final_trips.append(each_trip.id)
                elif source_id in city_seq.keys() and dest_id in city_seq.keys():
                    if city_seq[source_id] < city_seq[dest_id]:
                        final_trips.append(each_trip.id)
                elif source_id in city_seq.keys() and dest_id == trip_dest:
                    final_trips.append(each_trip.id)
        # Remove Old Trips
        for et in trip_obj.browse(final_trips):
            if datetime.strptime(et.start_time, '%Y-%m-%d %H:%M:%S') < datetime.today():
                try:
                    final_trips.pop(final_trips.index(et.id))
                except:
                    pass
        return {'domain': {'return_trip_id': [('id', 'in', final_trips)], 'return_park_loc_id': [('id', 'in', return_park_ids)]}, \
                'value': {'return_trip_id': final_trips and final_trips[0] or False, 'return_park_loc_id': default_location and default_location[0] or False}}

    @api.one
    def _computing_date_user(self):
        # check this remaining
        self.booking_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self.booking_user = self._uid
        return True

    @api.multi
    def _get_user_city(self):
        users_obj = self.env['res.users'].browse(self._uid)
        if users_obj.parking_city_id:
            return users_obj.parking_city_id.id
        return False

    @api.multi
    def _get_user_arrival_city(self):
        users_obj = self.env['res.users'].browse(self._uid)
        if users_obj.default_arrival_city_id:
            return users_obj.default_arrival_city_id.id
        return False

    @api.onchange('cust_phone_no')
    def onchange_cust_mobile_no(self):
        if self.cust_phone_no:
            customer_id = self.env['res.partner'].search([('phone', '=', self.cust_phone_no)])
            if customer_id and len(customer_id) == 1:
                self.customer_id = customer_id.id
            elif customer_id and len(customer_id) > 1:
                self.customer_id = customer_id[0].id

    @api.model
    def default_get(self, fields):
        trip_seat = []
        res = super(fleet_trip_reservation, self).default_get(fields)
        if res.get('trip_date') and (res.get('trip_date') != datetime.strftime(date.today(), '%Y-%m-%d')):
            res.update({'trip_date' : datetime.strftime(date.today(), '%Y-%m-%d')})
        return res

    name = fields.Char('Name', readonly=True, copy=False)
    booking_date = fields.Datetime(
        'Booking Date', help="Date on which the customer comes to book the ticket", readonly=True, copy=False)
    booking_user = fields.Many2one('res.users', 'Booking User', readonly=True, copy=False)
    trip_date = fields.Date('Trip Date', default=date.today())
    cust_phone_no = fields.Char(string="Phone No.")
    customer_id = fields.Many2one('res.partner', "Customer", required=True)
    source_id = fields.Many2one('fleet.city', 'Source Point', required=True, default=_get_user_city)
    dest_id = fields.Many2one('fleet.city', 'Destination Point', required=True, default=_get_user_arrival_city)
    total_price = fields.Float('Total', copy=False)
#     total_amt = fields.Float('Total')
    seat_ids = fields.One2many('trip.reservation.seat', 'reservation_id', "Seat Details", copy=False)
    luggage_ids = fields.One2many('trip.luggage', 'reservation_id', string="Luggage Details", copy=False)
    trip_id = fields.Many2one('fleet.trip', "Trip", readonly=False, context={'from_res': True},)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('cancelled', 'Cancelled'), ], 'State', default="draft", copy=False)
#     fare_id = fields.Many2one('trip.config.fare', 'Fare from',)
    pricelist_id = fields.Many2one(
        'product.pricelist', "Pricelist", invisible=True)
    product_id = fields.Many2one('product.product', "product", invisible=True)
    # return trip fields
    return_trip = fields.Boolean('Return Trip')
    return_date = fields.Date('Return Date',)
    return_trip_id = fields.Many2one('fleet.trip', "Return Trip", readonly=False,)
    parking_loc_id = fields.Many2one('fleet.parking.location', string='Boarding Location')
    return_park_loc_id = fields.Many2one('fleet.parking.location', string='Return Boarding Location')
    invoice_id = fields.Many2one('account.invoice', string="Invoice ID")

    @api.model
    def create(self, vals):
        if not vals.get('seat_ids'):
            raise Warning(_("Please, select seat(s) to book."))
#         if not vals.get('trip_date'):
#             vals.update({'trip_date' : datetime.strftime(date.today(), '%Y-%m-%d')})
        if self._context.get('from_cloud'):
            return super(fleet_trip_reservation, self).create(vals)
        else:
            fleet_trip_obj = self.env['fleet.trip']
            vals['name'] = self.env['ir.sequence'].get('trip_booking')
            vals['booking_user'] = self._uid
            vals['booking_date'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            if vals.get('trip_date'):
                if (date.today() > datetime.strptime(vals.get('trip_date'), '%Y-%m-%d').date()):
                    raise RedirectWarning(_('Trip Date should be greater then Today..!'))
            if vals.get('return_date') and vals.get('return_trip'):
                if (date.today() > datetime.strptime(vals.get('return_date'), '%Y-%m-%d').date()):
                    raise RedirectWarning(_('Return Trip date should be greater then Today..!'))
            if not vals.get('return_date') and vals.get('return_trip_id') and vals.get('return_trip'):
                raise RedirectWarning(_('Return Trip should have a date..!'))
            if vals.get('trip_date') and vals.get('return_date') and vals.get('return_trip'):
                if datetime.strptime(vals.get('trip_date'), '%Y-%m-%d').date() > \
                    datetime.strptime(vals.get('return_date'), '%Y-%m-%d').date():
                        raise RedirectWarning(_('Return Trip date should be greater then Trip Date..!'))
            ret_val = super(fleet_trip_reservation, self).create(vals)
            return ret_val

# ==========================INVOICE CCODE STARTS HERE==============================================================

    @api.multi
    def make_invoice_paid(self, invoice_ids):
        '''this is the method which make the invoice paid'''
        if invoice_ids:
            vals_acc_voucher = {}
            user_record = self.env['res.users'].browse([self._uid])
            invoice_brw = self.env['account.invoice'].browse(invoice_ids)
            account_voucher_obj = self.env['account.voucher']
            journal_id = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', user_record.company_id.id)], limit=1)
            all_fields = account_voucher_obj.fields_get([])
            default_get_invoice_payment = account_voucher_obj.with_context({'journal_id':journal_id.id}).default_get(all_fields.keys())
            if invoice_brw.partner_id and invoice_brw.partner_id.parent_id:
                customer_id = invoice_brw.partner_id.parent_id
            else:
                customer_id = invoice_brw.partner_id
            res_onchange_journal_id = account_voucher_obj.onchange_journal(
                                                                    journal_id=journal_id.id,
                                                                    line_ids=[(6, 0, [])],
                                                                    tax_id=[],
                                                                    partner_id=customer_id.id,
                                                                    date=date.today(),
                                                                    amount=invoice_brw.amount_total,
                                                                    ttype='sale',
                                                                    company_id=customer_id.company_id.id,
                                                                )
            res_onchange_amount = account_voucher_obj.onchange_amount(
                                                        amount=invoice_brw.amount_total,
                                                        rate=1.0,
                                                        journal_id=journal_id.id,
                                                        partner_id=customer_id.id,
                                                        currency_id=customer_id.company_id.currency_id.id,
                                                        ttype='sale', date=date.today(),
                                                        payment_rate_currency_id=customer_id.company_id.currency_id.id,
                                                        company_id=False)
            vals_acc_voucher.update(res_onchange_amount['value'])
            line_cr_ids, line_dr_ids = [], []
            for each_line in res_onchange_amount['value']['line_cr_ids']:
                line_cr_ids.append((0, 0, each_line))
            for dr_line in res_onchange_amount['value']['line_dr_ids']:
                line_dr_ids.append((0, 0, dr_line))
            vals_acc_voucher.update({'line_cr_ids': line_cr_ids, 'line_dr_ids': line_dr_ids})
            vals_acc_voucher.update(default_get_invoice_payment)
            vals_acc_voucher.update(res_onchange_journal_id['value'])
            vals_acc_voucher.update({'account_id': journal_id.default_debit_account_id.id})
            vals_acc_voucher.update({'reference': invoice_brw.origin,
                                    'partner_id': customer_id.id,
                                    'type': 'receipt'})
            account_voucher_rec = account_voucher_obj.create(vals_acc_voucher)
            account_voucher_rec.button_proforma_voucher()
        return True

    @api.v7
    def confirm_invoice(self, cr, uid, ids, invoice_ids):
        invoice_obj = self.pool.get('account.invoice')
        avl_obj = self.pool.get('account.voucher.line')
        if isinstance(invoice_ids, int):
            invoice_ids = [invoice_ids]
        self.make_invoice_paid(cr, uid, ids, invoice_ids)
        invoice_id = invoice_obj.browse(cr, uid, invoice_ids)
        if invoice_id and invoice_id.trip_book_id:
            template_obj = self.pool.get('email.template')
            if invoice_id.journal_id and invoice_id.journal_id.type == "sale":
                invoice_id.trip_book_id.write({'state': 'confirmed'})
                template_id = self.pool.get('email.template').browse(cr, uid, self.pool.get('ir.model.data').get_object_reference(cr, uid, 'spantree_logistics', 'spantree_logistics_email_send_tickets_template')[1])
                if template_id:
                    template_obj.send_mail(cr , uid, template_id.id, invoice_id.trip_book_id.id, True, context=None)
            elif invoice_id.journal_id and invoice_id.journal_id.type == "sale_refund":
                invoice_id.trip_book_id.write({'state': 'cancelled'})
                template_id = self.pool.get('email.template').browse(cr, uid, self.pool.get('ir.model.data').get_object_reference(cr, uid, 'spantree_logistics', 'spantree_logistics_email_send_refund_invoice_template')[1])
                if template_id:
                    template_obj.send_mail(cr , uid, template_id.id, invoice_id.id, True, context=None)
        return True
# =====================================INVOICE CODE END================================================================

    @api.v7
    def paid_invoice2(self, cr, uid, ids, invoice_id, context={}):
        self.confirm_invoice(cr, uid, ids, invoice_id)
        return True

    @api.v8
    def paid_invoice2(self, invoice_id,):
        # donot delete this method, if you don't know why its here
        invoice = self.env['account.invoice'].browse(invoice_id)
        invoice.signal_workflow('invoice_open')
        return self._model.paid_invoice2(self._cr, self._uid, self.id, invoice_id, context=self._context)

    @api.multi
    def make_payment(self):
        invoice_id = self.env['account.invoice'].search([('trip_book_id', '=', self.id), ('is_luggage', '=', False)])
        if invoice_id:
            raise Warning(_("Invoice is already created."))
        self.sudo().confirm_booking()
        invoice_id = self.sudo().create_cash_line()
        if invoice_id and invoice_id[0]:
            self.write({'invoice_id': invoice_id[0]})
            template_id = self.env.ref('spantree_logistics.spantree_logistics_email_send_invoice_template', False)
            if template_id:
                template_obj = self.pool.get('email.template')
                template_obj.send_mail(self._cr , self._uid, template_id.id, invoice_id[0], True, context=None)
            if self._uid == SUPERUSER_ID or self.pool['res.users'].has_group(self._cr, self._uid, 'spantree_logistics.group_cashier_user'):
                self.send_sms()
                self._model.paid_invoice2(self._cr, self._uid, self.id, invoice_id[0], context=self._context)
            view_id = self.env['ir.model.data'].get_object_reference('account', 'invoice_form')[1]
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'view_id': [view_id],
                'res_id': invoice_id[0] or False,
                'type': 'ir.actions.act_window',
            }
        return True

    @api.one
    def confirm_booking(self):
        # check if the seats are booked meanwhile
        seat_no = ''
        no_seat_available = []
        no_return_seat_available = []
        if not self.seat_ids:
            raise Warning("Please Book a seat first to Confirm.\n You can Input the seat from 'Input Seats' Button")
        for seat in self.seat_ids:
            seats_data = self.find_routewise_seats(self.source_id.id, self.dest_id.id, seat.trip_id.id)
            if (seat.source_id.id == self.source_id.id) and (seat.dest_id.id == self.dest_id.id):
                if seat.seat_no.id not in seats_data['free_seats']:
                    no_seat_available.append(seat.seat_no.seat_no)
        if no_seat_available:
            for x in no_seat_available:
                seat_no = seat_no + '' + str(x) + ','
            raise except_orm(_('Warning!'), ("Sorry, The Seats number %s have been allocated for the trip. Please try again, or check the Seat Status for more Information ") % (seat_no))
        if self.return_trip_id:
            for seat in self.seat_ids:
                seats_data = self.find_routewise_seats(self.dest_id.id, self.source_id.id, seat.trip_id.id)
                if (seat.source_id.id == self.dest_id.id) and (seat.dest_id.id == self.source_id.id):
                    if seat.seat_no.id not in seats_data['free_seats']:
                        no_return_seat_available.append(seat.seat_no.seat_no)
        if no_return_seat_available:
            for x in no_return_seat_available:
                seat_no = seat_no + '' + str(x) + ','
            raise except_orm(_('Warning!'), ("Sorry, The Seats number %s have been allocated for return trip. Please try again, or check the Seat Status for more Information ") % (seat_no))
#         self.paid_invoice2(invoice_id)
#         self.state = 'confirmed'
        return True

    @api.one
    def create_cash_line(self):
#         account_bank_statement_line_obj = self.env['account.bank.statement.line']
#         account_bank_statement_obj_id = self.env['account.bank.statement'].search([('user_id','=',self._uid),('date','=',date.today().strftime('%Y-%m-%d')),('state', '=', 'open')])
#         if not account_bank_statement_obj_id:
#                 raise except_orm(_('Cash Register Not Found'), 
#                                  ('please contact to admin to create cash register'))
#         account_bank_statement_line_obj.create({'date': self.booking_date,
#                                                 'name': 'Daily Trip' + '/' + self.name,
#                                                 'amount': self.total_price,
#                                                 'statement_id': account_bank_statement_obj_id.id,
#                                                 'ref': self.source_id.name,
#                                                 'partner_id': self.customer_id.id,
#                                                 })
#         return True
        vals = {}
        account_invoice_obj = self.env['account.invoice']
        account_invoice_line_obj = self.env['account.invoice.line']
        journal_id = account_invoice_obj._default_journal()
        currency_id = account_invoice_obj._default_currency()
        partner_brw = self.customer_id or self.env['ir.model.data'].get_object_reference(
            'spantree_logistics', 'res_partner_parking')[1]
        partner_onchange = account_invoice_obj.onchange_partner_id(
            type='out_invoice', partner_id=partner_brw.id)
        product_brw = self.env['product.product'].browse(self.env['ir.model.data'].get_object_reference('spantree_logistics', 'product_product_trip')[1])

        product_onchange = account_invoice_line_obj.product_id_change(product_brw.id, product_brw.uom_id.id,
                                                                      qty=0, name='', type='out_invoice', partner_id=partner_brw.id)
        product_vals = {
            'account_analytic_id': False,
            'account_id': product_onchange['value'] and product_onchange['value']['account_id'] or False,
            'discount': 0,
            'invoice_line_tax_id': [[6, False, []]],
            'name': self.name + ' ' + self.source_id.name + ' To ' + self.dest_id.name,
            'price_unit': self.total_price,
            'product_id': product_brw.id,
            'quantity': 1,
            'uos_id': product_brw.uom_id.id
        }
        vals.update({
            'partner_id': partner_brw.id,
            'name': self.customer_id.name or self.cust_name,
            'fiscal_position': partner_onchange['value']['fiscal_position'] and partner_onchange['value']['fiscal_position'] or False,
            'journal_id': journal_id and journal_id.id or False,
            'account_id': partner_onchange['value']['account_id'] and partner_onchange['value']['account_id'] or False,
            'currency_id': currency_id and currency_id.id or False,
            'company_id': self.env['res.company']._company_default_get('account.invoice'),
            'invoice_line': [(0, 0, product_vals)],
            'trip_book_id': self.id,
            'payment_term': partner_onchange['value']['payment_term'] and partner_onchange['value']['payment_term'] or False,
            'date_due': self.trip_date
        })
        invoice_brw = account_invoice_obj.create(vals)
        invoice_brw.signal_workflow('invoice_open')
        return invoice_brw.id

    @api.multi
    def stat_seats_reserved(self):
        trip_res = self.env['fleet.trip.reservation']

        if self._context.get('return_trip'):
            trip_id = self.return_trip_id.id
            seats_data = self.sudo().find_routewise_seats(self.dest_id.id, self.source_id.id, trip_id)
        else:
            trip_id = self.trip_id.id
            seats_data = self.sudo().find_routewise_seats(self.source_id.id, self.dest_id.id, trip_id)
        seat_ids = []
        for r in trip_res.sudo().browse(seats_data.get('clashed_trip_res_ids', [])):
            for seat_line in r.seat_ids:
                if seat_line.trip_id.id == trip_id:
                    seat_ids.append(seat_line.id)
        return {"type": "ir.actions.act_window",
                 "res_model": "trip.reservation.seat",
                 'view_type': 'form',
                 'view_mode': 'tree',
                 "target": "current",
                 'domain': [('id', 'in', seat_ids)]
                }

    @api.multi
    def action_view_invoice(self):
        view_id = self.env['ir.model.data'].get_object_reference('account', 'invoice_form')[1]
        invoice_id = self.env['account.invoice'].search([('trip_book_id', '=', self.id)])
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': [view_id],
            'res_id': invoice_id.id if invoice_id else False,
            'type': 'ir.actions.act_window',
        }

    @api.one
    def cancel_booking(self):
#         account_bank_statement_line_obj = self.env['account.bank.statement.line']
#         account_bank_statement_obj_id = self.env['account.bank.statement'].search([('user_id','=',self._uid),('date','=',date.today().strftime('%Y-%m-%d')),('state', '=', 'open')])
#         if not account_bank_statement_obj_id:
#             raise except_orm(_('Cash Register Not Found'), 
#                              ('please contact to admin to create cash register'))
#         account_bank_statement_line_obj.create({'date': self.booking_date,
#                                                 'name': 'Daily Trip' + '/' + self.name,
#                                                 'amount': -self.total_price,
#                                                 'statement_id': account_bank_statement_obj_id.id,
#                                                 'ref': self.source_id.name,
#                                                 'partner_id': self.customer_id.id,
#                                                 })
#         return self.write({'state': 'cancelled'})
        if self.trip_id and self.trip_id.start_time and self._context.get('tz'):
            tz = timezone(self._context.get('tz'))
            current_time = datetime.strptime(datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
            trip_date = datetime.strptime(self.trip_id.start_time, '%Y-%m-%d %H:%M:%S')
            if (trip_date - current_time).total_seconds() / 60 < 1440.00:
                raise Warning(_("Sorry, you can not cancel your tickets now. you can only cancel your booking before 24 hours of trip time."))
            self.state = "cancelled"
            invoice = self.env['account.invoice'].search([('trip_book_id', '=', self.id)])
            if invoice:
                acc_refund = self.env['account.invoice.refund']
                default_vals = acc_refund.default_get(['date', 'journal_id', 'filter_refund', 'description'])
                ref_id = acc_refund.create(default_vals)
                ctx = dict(self._context)
                ctx.update({'active_model': 'account.invoice',
                 'journal_type': 'sale', 'search_disable_custom_filters': True, 'active_ids': [invoice.id],
                 'type': 'out_invoice', 'active_id': invoice.id})
     
                refund_invoice_id = ''
                fields_get = ref_id.with_context(ctx).invoice_refund()
                if fields_get and fields_get.get('domain'):
                    for domain in fields_get['domain']:
                        if len(domain) > 2 and domain[0] == 'id':
                            refund_invoice_id = domain[2]
     
                    invoice = self.env['account.invoice'].browse(refund_invoice_id)
                    invoice.trip_book_id = self.id
                    invoice.signal_workflow('invoice_open')
                    self.write({'state': 'cancelled'})
                    return self._model.paid_invoice2(self._cr, self._uid, self.id, refund_invoice_id, context=self._context)
        return True

    @api.multi
    def send_sms(self, booking_id=None):
        if self._context.get('from_regi_payment'):
            trip_book_id = booking_id
        else:
            trip_book_id = self
        if trip_book_id.customer_id.mobile:
            messages = []
            trip_code = ''
            return_trip_code = ''
            message = ''
            if trip_book_id.return_trip:
                for line in trip_book_id.seat_ids:
                    if trip_book_id.trip_id == line.trip_id:
                        trip_code = trip_code + str(line.barcode) + ','
                    else:
                        return_trip_code = return_trip_code + str(line.barcode) + ','
                if trip_book_id.parking_loc_id and trip_book_id.return_park_loc_id:
                    message = trip_book_id.customer_id.name + ",ticket info.,Trip:" + trip_book_id.trip_id.name + ",Ticket Code:" + trip_code[:-1] + ",Boarding From:" + trip_book_id.parking_loc_id.name + ",Return Trip:" + trip_book_id.return_trip_id.name + ",Return Tickets Code:" + return_trip_code[:-1] + ",Boarding From:" + trip_book_id.return_park_loc_id.name
                elif trip_book_id.parking_loc_id:
                    message = trip_book_id.customer_id.name + ",ticket info.,Trip:" + trip_book_id.trip_id.name + ",Ticket Code:" + trip_code[:-1] + ",Boarding From: " + trip_book_id.parking_loc_id.name + ",Return Trip:" + trip_book_id.return_trip_id.name + ",Return Tickets Code:" + return_trip_code[:-1]
                elif trip_book_id.return_park_loc_id:
                    message = trip_book_id.customer_id.name + ",ticket info.,Trip:" + trip_book_id.trip_id.name + ",Ticket Code:" + trip_code[:-1] + ",Return Trip: " + trip_book_id.return_trip_id.name + ",Return Tickets Code:" + return_trip_code[:-1] + ",Boarding From:" + trip_book_id.return_park_loc_id.name
                else:
                    message = trip_book_id.customer_id.name + ",ticket info.,Trip:" + trip_book_id.trip_id.name + ",Ticket Code:" + trip_code[:-1] + ",Return Trip:" + trip_book_id.return_trip_id.name + ",Return Tickets Code:" + return_trip_code[:-1]
            else:
                for line in trip_book_id.seat_ids:
                    trip_code = trip_code + str(line.barcode) + ','
                if trip_book_id.parking_loc_id:
                    message = trip_book_id.customer_id.name + ",ticket info.,Trip:" + trip_book_id.trip_id.name + ",Ticket Code:" + trip_code[:-1] + ",Boarding From:" + trip_book_id.parking_loc_id.name
                else:
                    message = trip_book_id.customer_id.name + ",ticket info.,Trip:" + trip_book_id.trip_id.name + ",Ticket Code:" + trip_code[:-1]
            if message:
                if len(message) > 160:
                    message = textwrap.wrap(message, width=157)
                if isinstance(message, list):
                    for msg in message:
                        self.env['sms.config'].send_sms(int(trip_book_id.customer_id.mobile), msg + '...')
                else:
                    self.env['sms.config'].send_sms(int(trip_book_id.customer_id.mobile), message)
        return True


class trip_reservation_seat(models.Model):
    _name = "trip.reservation.seat"
    _order = "seat_no"
    # Reservation Detail Table

    
    @api.multi
    def action_update_trip(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_open_form_view(self):
        view_id = self.env['ir.model.data'].get_object_reference('spantree_logistics', \
                                            'trip_reservation_seat_form_for_line_view')[1]
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'trip.reservation.seat',
            'view_id': [view_id],
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target' : 'new',
        }

    @api.model
    def create(self, vals):
        if vals.get('no_of_seat'):
            if vals.get('no_of_seat') < 1:
                raise Warning(_('No of Seats must be grather then 0'))
            trip_input_seat_id = self.env['trip.input.seat'].create({'passenger_type': vals.get('passenger_type'),
                                                                     'no_of_seat' : vals.get('no_of_seat')})
            if trip_input_seat_id:
                ctx = dict(self._context)
                ctx.update({'active_ids': [vals.get('reservation_id')]})
                lines = trip_input_seat_id.with_context(ctx).sudo().reserve_seats()
                if lines:
                    if len(lines[0]) == 1:
                        brw_rec = self.browse([x.id for x in lines[0]])
                        if self._context.get('from_website'):
                            brw_rec.write({'name':vals.get('name')})
                        return brw_rec[0]
                    else:
                        brw_rec = self.browse([x.id for x in lines[0]])
                        for brw in brw_rec:
                            if self._context.get('from_website'):
                                brw.write({'name':vals.get('name')})
                        return brw_rec[0][0]
                else:
                    raise Warning("Values mismatch into seat creation!")
        else:
            return super(trip_reservation_seat, self).create(vals)

    @api.multi
    def write(self, vals):
        if self._context.get('from_cloud'):
            return super(trip_reservation_seat, self).write(vals)
        else:
            for seat_line in self.browse(self._ids):
                result = self.validate_trip_change(self.source_id, self.dest_id, self.reservation_id, self.trip_id)
                if result:
                    raise Warning("You can not change trip which already occured or expired...!")
            if vals.get('seat_no'):
                trip_id = vals.get('trip_id') if vals.get('trip_id') else self.trip_id.id
                seat_ids = self.search([('id', '!=', self.id), ('trip_id', '=', trip_id)])
                for seat in seat_ids:
                    if vals.get('seat_no') == seat.seat_no.id:
                        raise except_orm(_('Warning!'), ("You have assigned seat no. %d to multiple Passengers!") % (int(vals.get('seat_no'))))
            return super(trip_reservation_seat, self).write(vals)

    @api.multi
    def validate_trip_change(self, source_id, dest_id, reservation_id, trip_id):
        '''validate that trip should be changed on validate time
        for both trip and return trip'''
        current_date = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        current_date = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
        if reservation_id.state == 'confirmed':
            if (reservation_id.source_id.id == source_id.id) and \
                (reservation_id.dest_id.id == dest_id.id):
                if current_date and trip_id.start_time and (current_date >= datetime.strptime(trip_id.start_time, '%Y-%m-%d %H:%M:%S')):
                    return True
            elif (reservation_id.dest_id.id == source_id.id) and \
                (reservation_id.source_id.id == dest_id.id):
                if current_date >= datetime.strptime(trip_id.start_time, '%Y-%m-%d %H:%M:%S'):
                    return True
                if (date.today() - datetime.strptime(reservation_id.trip_date, '%Y-%m-%d').date()).days > 30:
                    return True
        return False

    @api.multi
    def onchange_seat_trip_fill(self, trip_id):
        '''if trip into reservation details change seat no will become blank'''
        result = self.validate_trip_change(self.source_id, self.dest_id, self.reservation_id, self.trip_id)

        msg = ''
        if result:
            raise RedirectWarning('You can not change trip which already occured or expired...!')
        if self.trip_id.id != trip_id:
            return {'value' : {'seat_no': False}}
        else:
            return {'value': {'seat_no': self.seat_no}}

    @api.model
    def _default_trip(self):
        if self._context.get('params') and self._context['params'].get('id'):
            trip_id = self.env['fleet.trip.reservation'].browse(
                self._context['params'].get('id')).trip_id.id
            return trip_id
        return False


    @api.model
    def _get_default_type(self):
        return self.env['ir.model.data'].get_object_reference('spantree_logistics', 'passenger_type_adult')[1]

    @api.one
    @api.depends('passenger_type')
    def _get_price(self):
        # TODO: can create a function that takes trip_id, source, dest, and return us price
        price = 0
        trip_fare = self.env['trip.config.fare']
        trip_reservation = self.reservation_id
        if not self.reservation_id.return_trip:
            fare = trip_fare.search([('route_id', '=', trip_reservation.trip_id.route_id.id)])
            if fare:
                for all_fares in fare.fare_lines:
                    if all_fares.from_city == trip_reservation.source_id and all_fares.to_city == trip_reservation.dest_id and not all_fares.round_trip:
                        for ptype in all_fares.passenger_types:
                            if ptype == self.passenger_type:
                                price = all_fares.price
                                self.price = price
                if not price:
                    model, action_id = self.env['ir.model.data'].get_object_reference('spantree_logistics', 'trip_config_fare_act')
                    msg = _('Oops !, No Fare set for this Passenger type for Source city %s and Dest. City %s in Route %s' \
                                    % (trip_reservation.source_id.name, trip_reservation.dest_id.name, trip_reservation.trip_id.route_id.name))
                    raise RedirectWarning(msg, action_id, _('Go to the Fare Settings'))
        else:
            fare = trip_fare.search([('route_id', '=', trip_reservation.trip_id.route_id.id)])
            if self.trip_id == trip_reservation.trip_id:
                if fare:
                    for all_fares in fare.fare_lines:
                        if all_fares.from_city == trip_reservation.source_id and all_fares.to_city == trip_reservation.dest_id and all_fares.round_trip:
                            for ptype in all_fares.passenger_types:
                                if ptype == self.passenger_type:
                                    price = all_fares.price
                                    self.price = price
                    if not price:
                        model, action_id = self.env['ir.model.data'].get_object_reference('spantree_logistics', 'trip_config_fare_act')
                        msg = _('Oops !, No Fare set for this Passenger type for Source city %s and Dest. City %s in Route %s' \
                                        % (trip_reservation.source_id.name, trip_reservation.dest_id.name, trip_reservation.trip_id.route_id.name))
                        raise RedirectWarning(msg, action_id, _('Go to the Fare Settings'))
        return True

    name = fields.Char('Passenger Name')
    passenger_type = fields.Many2one('passenger.type', 'Passenger Type', required=True, default=_get_default_type)
    seat_qty = fields.Integer('No. of Seats', readonly=True, default=1)
    price = fields.Float('Price', readonly=True, compute=_get_price, store=True)
    reservation_id = fields.Many2one('fleet.trip.reservation', "Reservation", ondelete='cascade')
    seat_no = fields.Many2one('fleet.vehicle.seat', 'Seat No.', required=True)
    trip_id = fields.Many2one('fleet.trip', "Trip", default=_default_trip)
    source_id = fields.Many2one('fleet.city', 'Source City', readonly=False)
    dest_id = fields.Many2one('fleet.city', 'Dest. City', readonly=False)
    board_loc_id = fields.Many2one('fleet.parking.location', string='Boarding Location')
    no_of_seat = fields.Integer(string="No. of Seat", default=1)
    barcode = fields.Char(string="Barcode")


#     _sql_constraints = [
#         ('seq_seat_uniq', 'unique (seat_no,reservation_id)', 'The Seat Number of the Trip  must be unique per Reservation.')
#     ]


class fleet_trip(models.Model):
    _name = "fleet.trip"
    _order = 'id desc'

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(fleet_trip, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(fleet_trip, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(fleet_trip, self).unlink()

    @api.multi
    def stat_seats_reserved(self):
        trip_res = self.env['fleet.trip.reservation']
        trip_id = self.route_id
        seats_data = trip_res.find_routewise_seats(trip_id.city_source.id, trip_id.city_destination.id, self.id)
        seat_ids = []
        for r in trip_res.browse(seats_data.get('clashed_trip_res_ids', [])):
            for seat_line in r.seat_ids:
                if seat_line.trip_id.id == self.id:
                    seat_ids.append(seat_line.id)
        return {"type": "ir.actions.act_window",
                 "res_model": "trip.reservation.seat",
                 'view_type': 'form',
                 'view_mode': 'tree',
                 "target": "current",
                 'domain': [('id', 'in', seat_ids)]
                }

    @api.one
    @api.depends('start_time', 'route_id')
    def _compute_trip_name(self):
        if self.start_time and self.route_id:
            self.name = "%s - %s" % (self.route_id.name, self.start_time,)
        return True

    name = fields.Char('Code', compute=_compute_trip_name, store=True)
    start_time = fields.Datetime('Departure Time', required=True)
    end_time = fields.Datetime('Arrival Time',)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle',)
    route_id = fields.Many2one('fleet.route', "Route", required=True)
    server_id = fields.Integer('Server ID')

    _sql_constraints = [
        ('name', 'unique(name)', 'Fleet Trip must be unique !')
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        res = []
        if self._context.get('trip_lines') and self._context.get('source_id') and self._context.get('dest_id'):
            fleet_reser_obj = self.env['fleet.trip.reservation']
            recs = fleet_reser_obj.onchange_fill_trip(source_id=self._context.get('source_id'), dest_id=self._context.get('dest_id'), \
                                                      trip_date=False, trip_id=False)
            recs = recs['domain']['trip_id'][0][2]
            recs = self.search([('id', 'in', recs)])
        elif self._context.get('from_boarding_line') and self._context.get('trip_id'):
            args = [('id', '=', self._context.get('trip_id'))]
            recs = self.search([('name', operator, name)] + args, limit=limit)
        elif self._context.get('from_luggage') and (self._context.get('trip_id') or self._context.get('return_trip_id')):
            recs = []
            recs = self.search([('id', 'in', [self._context.get('return_trip_id'), self._context.get('trip_id')])] + args, limit=limit)
        else:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        trip_res = self.env['fleet.trip.reservation']
        if self._context.get('from_trip_booking'):
            result = []
            for rec in self:
                seats_data = trip_res.find_routewise_seats(rec.route_id.city_source.id, rec.route_id.city_destination.id, rec.id)
                total_free = len(seats_data['free_seats'])
                name_split = rec.name.split('-')
                date_time_split = name_split[4].split(' ')
                result.append((rec.id, "%s" % (date_time_split[0].strip() + '/' + name_split[3].strip() + '/' + name_split[2].strip()\
                                               + ' ' + str(date_time_split[1]).strip() + ' (Seats ' + str(total_free).strip() + ')' or '')))
        else:
            result = super(fleet_trip, self).name_get()
        return result

class fleet_trip_config(models.Model):
    _name = "fleet.trip.config"

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(fleet_trip_config, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(fleet_trip_config, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(fleet_trip_config, self).unlink()

#     trip_days_line = fields.One2many('fleet.trip.config.line', 'trip_config_id', 'Trip Lines')
    trip_time_line = fields.One2many(
        'fleet.trip.config.line', 'trip_config_id', 'Time Lines')
    active_status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Active Status', default='active', required=True)
    trips_created_till = fields.Date('Trips Created Upto', required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle',)
    route_id = fields.Many2one('fleet.route', "Route", required=True)
    server_id = fields.Integer('Server ID')

#     @api.one
#     def schedule_trips(self):
#         """
#         Creates daily trips for each trip.config record for the 15th day from today.
#         If scheduler runs for first time. it will create trips from today to next 15 days, as per the Time Lines given
#         """
#         # TODO: fix timezone increment issue.
#         fleet_trip = self.env['fleet.trip']
#         trip_configs = self.search([('active_status', '=', 'active')])
#         for conf in trip_configs:
#             if conf.trips_created_till:
#                 trip_created_upto = datetime.date(datetime.strptime(conf.trips_created_till, '%Y-%m-%d'))
#                 next_day = trip_created_upto + timedelta(days=1)
#                 for day_line in conf.trip_time_line:
#                     if day_line.trip_day == next_day.strftime('%a'):
#                         fleet_trip.create({'route_id': conf.route_id.id,
#                                             'start_time': (datetime(year=next_day.year, month=next_day.month, day=next_day.day,) + timedelta(hours=day_line.start_hour)).strftime('%Y-%m-%d %H:%M:%S'),
#                                            'end_time': (datetime(year=next_day.year, month=next_day.month, day=next_day.day,) + timedelta(hours=(day_line.start_hour + day_line.travel_hour)).strftime('%Y-%m-%d %H:%M:%S')) if day_line.travel_hour else False,
#                                            'vehicle_id': conf.vehicle_id.id if conf.vehicle_id else False, })
#                 conf.write({'trips_created_till': next_day.strftime('%Y-%m-%d')})
#             else:
#                 for each_day in range(0, 16):
#                     next_day = datetime.date(datetime.today() + timedelta(days=each_day))
#                     for day_line in conf.trip_time_line:
#                         if day_line.trip_day == next_day.strftime('%a'):
#                             fleet_trip.create({'route_id': conf.route_id.id,
#                                                'start_time': (datetime(year=next_day.year, month=next_day.month, day=next_day.day,) + timedelta(hours=day_line.start_hour)).strftime('%Y-%m-%d %H:%M:%S'),
#                                                'end_time': (datetime(year=next_day.year, month=next_day.month, day=next_day.day,) + timedelta(hours=(day_line.start_hour + day_line.travel_hour))).strftime('%Y-%m-%d %H:%M:%S') if day_line.travel_hour else False,
#                                                'vehicle_id': conf.vehicle_id.id if conf.vehicle_id else False, })
#                 conf.write({'trips_created_till': datetime.date(datetime.today() + timedelta(days=15)).strftime('%Y-%m-%d')})
#         return True

    @api.model
    def schedule_trips(self):
        """
        Creates daily trips for each trip.config record for the 15th day from today.
        If scheduler runs for first time. it will create trips from today to next 15 days, as per the Time Lines given
        """
        # TODO: fix timezone increment issue.
        fleet_trip = self.env['fleet.trip']
        trip_configs = self.search([('active_status', '=', 'active')])
        for conf in trip_configs:
            if conf.trips_created_till:
                trip_created_upto = datetime.date(datetime.strptime(conf.trips_created_till, '%Y-%m-%d'))
                next_day = trip_created_upto + timedelta(days=1)
                for day_line in conf.trip_time_line:
                    if day_line.trip_day == next_day.strftime('%a'):
                        fleet_trip.create({'route_id': conf.route_id.id,
                                            'start_time': (datetime(year=next_day.year, month=next_day.month, day=next_day.day,) + timedelta(hours=day_line.start_hour)).strftime('%Y-%m-%d %H:%M:%S'),
                                           'end_time': (datetime(year=next_day.year, month=next_day.month, day=next_day.day,) + timedelta(hours=(day_line.start_hour + day_line.travel_hour))).strftime('%Y-%m-%d %H:%M:%S') if day_line.travel_hour else False,
                                           'vehicle_id': conf.vehicle_id.id if conf.vehicle_id else False, })
                conf.write({'trips_created_till': next_day.strftime('%Y-%m-%d')})
            else:
                for each_day in range(0, 16):
                    next_day = datetime.date(datetime.today() + timedelta(days=each_day))
                    for day_line in conf.trip_time_line:
                        if day_line.trip_day == next_day.strftime('%a'):
                            fleet_trip.create({'route_id': conf.route_id.id,
                                               'start_time': (datetime(year=next_day.year, month=next_day.month, day=next_day.day,) + timedelta(hours=day_line.start_hour)).strftime('%Y-%m-%d %H:%M:%S'),
                                               'end_time': (datetime(year=next_day.year, month=next_day.month, day=next_day.day,) + timedelta(hours=(day_line.start_hour + day_line.travel_hour))).strftime('%Y-%m-%d %H:%M:%S') if day_line.travel_hour else False,
                                               'vehicle_id': conf.vehicle_id.id if conf.vehicle_id else False, })
                conf.write({'trips_created_till': datetime.date(datetime.today() + timedelta(days=15)).strftime('%Y-%m-%d')})
        return True

class fleet_trip_config_line(models.Model):
    _name = "fleet.trip.config.line"

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(fleet_trip_config_line, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(fleet_trip_config_line, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(fleet_trip_config_line, self).unlink()

    trip_config_id = fields.Many2one(
        'fleet.trip.config', "Trip Configuration", required=True)
    trip_day = fields.Selection([('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'), ('Thu', 'Thursday'),
                                 ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday'), ], 'Week Day', required=True)
#     start hour and travel hour below
    start_hour = fields.Float('Start Hour', required=True)
    travel_hour = fields.Float('Travelling Time (in Hrs.)', help="To Calculate Arrival Time for trip Created")
    active_status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], 'Active Status', default='active', required=True)
    server_id = fields.Integer('Server ID')


class trip_config_fare(models.Model):
    _name = "trip.config.fare"
    # use fare in creating trips from scheduler, and also when inputing the
    # seat info in trip

    @api.one
    @api.depends('route_id')
    def _compute_fare_name(self):
        if self.route_id:
            self.name = "Fare for %s " % self.route_id.name
        return True

    name = fields.Char('Fare Name', compute=_compute_fare_name,)
    fare_lines = fields.One2many('trip.config.fare.line', 'fare_id', 'Fare Details')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle',)
    route_id = fields.Many2one('fleet.route', "Route")
    server_id = fields.Integer('Server ID')

    _sql_constraints = [
        ('name', 'unique(name)', 'Trip Config Fare must be unique !')
    ]

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(trip_config_fare, self).create(vals)

    @api.multi
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(trip_config_fare, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(trip_config_fare, self).unlink()


class passenger_type(models.Model):
    _name = 'passenger.type'

    # TODO: add this object in config. menu of transport
    name = fields.Char('Name', required=True)
# 
#     _sql_constraints = [
#         ('name', 'unique(name)', 'Passenger Type must be unique !')
#     ]


class trip_config_fare_line(models.Model):
    _name = "trip.config.fare.line"

    @api.one
    @api.constrains('price')
    def check_rate(self):
        if self.price and self.price < 0.0:
            raise Warning(_('Price for the trip can not be zero(0).'))

    fare_id = fields.Many2one('trip.config.fare', 'Fare To Use')
    passenger_types = fields.Many2many('passenger.type', 'fare_rel_passenger_type', 'fare_id', 'type_id', 'Passenger Type')
    price = fields.Float('Price')
    from_city = fields.Many2one('fleet.city', 'From City')
    to_city = fields.Many2one('fleet.city', 'To City')
    round_trip = fields.Boolean('Round Trip')
    server_id = fields.Integer('Server ID')

    @api.multi
    def onchange_city(self, from_city, to_city, field, route_id):
        # TODO: Right now Only from_city onchange handled, later we can add
        # to_city also.
        if route_id:
            route = self.env['fleet.route'].browse(route_id)
            if from_city and not to_city:
                to_cities = []
                if from_city == route.city_destination.id:
                    raise Warning(
                        "Destination City cannot be Start Point! Please add according to Sequence in Route Points")
                if from_city == route.city_source.id:
                    to_cities = []
                    to_cities = [x.city_id.id for x in route.route_point_ids]
                    to_cities.append(route.city_destination.id)
# return {'domain': {'to_city': [('id', 'in', to_cities)]}, 'value': {}}
                elif from_city in [x.city_id.id for x in route.route_point_ids]:
                    to_cities = []
                    match_seq = False
                    for each_point in route.route_point_ids:
                        if from_city == each_point.city_id.id:
                            match_seq = each_point.sequence_no
                    for each_point in route.route_point_ids:
                        if each_point.sequence_no > match_seq:
                            to_cities.append(each_point.city_id.id)
                    to_cities.append(route.city_destination.id)
                return {'domain': {'to_city': [('id', 'in', to_cities)]}, 'value': {}}
        return {}

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(trip_config_fare_line, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(trip_config_fare_line, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(trip_config_fare_line, self).unlink()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
