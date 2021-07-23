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
from openerp import SUPERUSER_ID
from datetime import datetime, date


class fleet_vehicle_type(models.Model):
    _name = 'fleet.vehicle.type'

    code = fields.Char('Code')
    name = fields.Char('Name')
    description = fields.Text(string='Description')


class fleet_vehicle_seat(models.Model):
    _name = "fleet.vehicle.seat"

    @api.multi
    @api.depends('seat_no')
    def name_compute(self):
        for each_self in self:
            each_self.name = each_self.seat_no

    seat_no = fields.Char('Seat No.', required=True, readonly=True)
    name = fields.Char(string='Name', compute= 'name_compute', store=True, readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', "Vehicle")

    _rec_name = 'seat_no'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        '''find the seat number base on trip id of reservation line'''
        args = args or []
        if self._context.get('from_trip_res') and self._context.get('dest_id') and self._context.get('source_id') and\
             self._context.get('trip_id'):
#             res_seat = self.env['trip.reservation.seat']
            trip_res = self.env['fleet.trip.reservation']
#             reservation = res_seat.browse(self._context.get('seat_line_id'))
            seats_data = trip_res.find_routewise_seats(self._context.get('source_id'), self._context.get('dest_id'),self._context.get('trip_id'))
            args.append(('id', 'in', seats_data.get('free_seats')))
            recs = self.browse(seats_data.get('free_seats'))
        elif self._context.get('from_boarding_line') and self._context.get('dest_id') and self._context.get('source_id') and\
             self._context.get('trip_id'):
            trip_res = self.env['fleet.trip.reservation']
            seats_data = trip_res.find_routewise_seats(self._context.get('source_id'), self._context.get('dest_id'),self._context.get('trip_id'))
            args.append(('id', 'in', seats_data.get('free_seats')))
            recs = self.browse(seats_data.get('free_seats'))
        elif self._context.get('from_luggage') and self._context.get('dest_id') and self._context.get('source_id') and\
             self._context.get('trip_id') and self._context.get('booking_number'):
            trip_res = self.env['fleet.trip.reservation']
            seats_data = trip_res.search([('name', '=', self._context.get('booking_number'))]).seat_ids
            seat_ids = [each_seat_data.seat_no.id for each_seat_data in seats_data]
            args.append(('id', 'in', seat_ids))
            recs = self.browse(seat_ids)
        else:
            recs = self.browse()  # blank browse, so no seats visible
        return recs.name_get()


class fleet_vehicle(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(fleet_vehicle, self).name_search(name, args, operator, limit)
        if self._context.get('from_vehicle_booking'):
            if not self._context.get('start_date') and not self._context.get('end_date'):
                raise Warning(_('Select Start date and End date for vehicle booking.'))
            res = self.check_vehicle_overlap(self._context.get('start_date'), self._context.get('end_date'))
        return res

    def check_vehicle_overlap(self, start_date, end_date):
        start_date = datetime.strptime(start_date,'%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(end_date,'%Y-%m-%d %H:%M:%S')
        vehicle_booking_obj = self.env['fleet.vehicle.booking']
        vehicle_obj = self.env['fleet.vehicle']
        result = []
        for vehicle in vehicle_obj.search([('state_id.id', '=', '2'), ('is_leasable', '=', True)]):
            flag = True
            vehicle_book_ids = self.env['fleet.vehicle.booking'].search([('vehicle_id', '=', vehicle.id),('state','in', ('confirmed', 'in_progress'))])
            for vehicle_book_id in vehicle_book_ids:
                if vehicle_book_id.state != 'in_progress':
                    if datetime.strptime(vehicle_book_id.start_date,'%Y-%m-%d %H:%M:%S') >= start_date and \
                        datetime.strptime(vehicle_book_id.end_date,'%Y-%m-%d %H:%M:%S') <= end_date:
                        flag = False
                    elif datetime.strptime(vehicle_book_id.start_date,'%Y-%m-%d %H:%M:%S') <= start_date and \
                        datetime.strptime(vehicle_book_id.end_date,'%Y-%m-%d %H:%M:%S') >= end_date:
                        flag = False
                    elif datetime.strptime(vehicle_book_id.start_date,'%Y-%m-%d %H:%M:%S') <= start_date and \
                        datetime.strptime(vehicle_book_id.end_date,'%Y-%m-%d %H:%M:%S') >= start_date:
                        flag = False
                    elif datetime.strptime(vehicle_book_id.start_date,'%Y-%m-%d %H:%M:%S') <= end_date and \
                        datetime.strptime(vehicle_book_id.end_date,'%Y-%m-%d %H:%M:%S') >= end_date:
                        flag = False
                else:
                    flag = False
            if flag:
                result.append((vehicle.id, vehicle.name))
        return result


    vehicle_type = fields.Many2one('fleet.vehicle.type', 'Vehicle Type')
    seat_prefix = fields.Char('Seat Prefix')
    no_of_seat = fields.Integer('No. of Seats')
    seat_nos = fields.One2many('fleet.vehicle.seat', 'vehicle_id', "Seat No.s")
    day_charge = fields.Float('Per Day Charge')
    seat_active = fields.Boolean('Active This Seats', default=False)
    is_leasable = fields.Boolean(string='Is Leasable')
    employee_driver_id = fields.Many2one('hr.employee', string="Employee Driver")

    @api.one
    def generate_seats(self):
        if self.no_of_seat:
            seat_names = {'seat_nos': []}
            for each in range(1, self.no_of_seat + 1):
                seat_names['seat_nos'].append((0, 0, {'seat_no': str(self.seat_prefix or '').strip() + str(each), 'vehicle_id':self.id}))
            self.write(seat_names)
        return True

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        if vals.get('license_plate'):
            vehicle_ids = self.search([('license_plate', '=', vals.get('license_plate'))])
            if vehicle_ids:
                raise Warning(_('Two Vehicles can not have same license plate no.'))
        if vals.get('employee_driver_id'):
            vehicle_ids = self.search([('employee_driver_id', '=', vals.get('employee_driver_id'))])
            if vehicle_ids:
                raise Warning(_('Same driver can not assign to multiple vehicles.'))
        return super(fleet_vehicle, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        if vals.get('license_plate'):
            license_plate = vals.get('license_plate') or self.license_plate
            if license_plate:
                vehicle_ids = self.search([('license_plate', '=', vals.get('license_plate'))])
                if vehicle_ids:
                    raise Warning(_('Two Vehicles can not have same license plate no.'))
        if vals.get('employee_driver_id'):
            employee_driver_id = vals.get('employee_driver_id') or self.employee_driver_id.id if self.employee_driver_id else False
            vehicle_ids = self.search([('employee_driver_id', '=', employee_driver_id)])
            if vehicle_ids:
                raise Warning(_('Same driver can not assign to multiple vehicles.'))
        return super(fleet_vehicle, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'), 
                            ('please contact to admin to delete a record'))
        for vehicle in self:
            if vehicle.seat_nos:
                vehicle.seat_nos.unlink()
        return super(fleet_vehicle, self).unlink()


class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'

    fleet_id = fields.Many2one('fleet.vehicle', "Vehicle")


class fleet_city(models.Model):
    _name = 'fleet.city'

    name = fields.Char('City Name', required=True)
    post_code = fields.Char('Zip Code')
    state_id = fields.Many2one('res.country.state', 'State')
    country_id = fields.Many2one('res.country', 'Country')
    location_id = fields.Many2one('stock.location', 'Location')
    server_id = fields.Integer('Server ID')

    _sql_constraints = [
        ('name', 'unique(name)', 'Fleet City must be unique !')
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.search([])
        if self._context.get('return_trip'):
            recs = self.search([('id', 'in', [self._context.get('dest_id'), self._context.get('source_id')])] + args, limit=limit)
        elif self._context.has_key('from_trip_fare_config') and self._context.has_key('route_id'):
            city_ids = [each_id.city_id.id for each_id in self.env['fleet.route'].browse(self._context.get('route_id')).route_point_ids]
            recs = self.search([('id', 'in', city_ids)] + args, limit=limit)
        elif not self._context.get('return_trip') and not self._context.get('from_luggage'):
            if self._context.get('source'):
                recs = self.search([('id', '=', self._context.get('source_id'))] + args, limit=limit)
            elif self._context.get('dest_id'):
                recs = self.search([('id', '=', self._context.get('dest_id'))] + args, limit=limit)
        elif self._context.get('from_luggage') and (self._context.get('destination_id') or self._context.get('source_id')):
            recs = []
            recs = self.search([('id', 'in', [self._context.get('destination_id'),self._context.get('source_id')])] + args, limit=limit)
        else:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.model
    def create(self, values):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        location = self.env['stock.location'].create({'loc_barcode': False, 'scrap_location': False, 'valuation_in_account_id': False, 'name': values.get('name', ''), 'location_id': False, 'company_id': 1, 'putaway_strategy_id': False, 'active': True, 'posz': 0, 'posx': 0, 'posy': 0, 'usage': 'internal', 'valuation_out_account_id': False, 'partner_id': False, 'comment': False, 'removal_strategy_id': False})
        values.update({'location_id': location.id})
        id = super(fleet_city, self).create(values)
        return id

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(fleet_city, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(fleet_city, self).unlink()


class Country(models.Model):
    _inherit = "res.country"
# 
#     phone2 = fields.Char(string="Phone 2")
#     server_id = fields.Integer('Server ID')

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(Country, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(Country, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(Country, self).unlink()


class stock_location(models.Model):
    _inherit = 'stock.location'

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(stock_location, self).create(vals)
 
    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(stock_location, self).write(vals)
 
    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(stock_location, self).unlink()


class CountryState(models.Model):
    _inherit = 'res.country.state'

    server_id = fields.Integer('Server ID')

    @api.model
    def create(self, vals):
#         res = []
# #         if vals.get('name'):
#         if self.search([('name','!=',vals.get('name'))]):
# #             if not get:
#             res = super(CountryState, self).create(vals)
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(CountryState, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(CountryState, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(CountryState, self).unlink()


class fleet_route_point(models.Model):
    _name = "fleet.route.point"

    @api.one
    @api.depends('city_id')
    def _compute_route_name(self):
        if self.city_id:
            self.name = "%s - Point" % self.city_id
        return True

    name = fields.Char('Point Name')
    city_id = fields.Many2one('fleet.city', 'City Name', required=True)
    arrival_time = fields.Datetime('Arrival Time')
    departure_time = fields.Datetime('Departure Time')
    hold_time = fields.Datetime('Hold Time')
    sequence_no = fields.Integer('Trip Sequence', required=True,
                                 help='Please input seq. in points as they come from source city to Dest. City')
    route_id = fields.Many2one('fleet.route', 'Route',)

    _sql_constraints = [
        ('seq_route_uniq', 'unique (sequence_no,route_id)', 'The Sequence of the Route Points must be unique per Route !')
    ]

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(fleet_route_point, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(fleet_route_point, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(fleet_route_point, self).unlink()


class fleet_route(models.Model):
    _name = "fleet.route"

    @api.one
    @api.depends('city_source', 'city_destination')
    def _compute_route_name(self):
        if self.city_destination and self.city_source:
            self.name = "%s - %s" % (self.city_source.name, self.city_destination.name)
        return True

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(fleet_route, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(fleet_route, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(fleet_route, self).unlink()

    name = fields.Char('Route name', compute=_compute_route_name, store=True)
    city_source = fields.Many2one('fleet.city', "Source Location", required=True)
    city_destination = fields.Many2one('fleet.city', "Destination Location", required=True)
    route_point_ids = fields.One2many('fleet.route.point', 'route_id', 'Route Points')
#     route_price = fields.One2many('fleet.route.price', 'route_id', 'Route Price')

    _sql_constraints = [
        ('name', 'unique(name)', 'Fleet Route must be unique !')
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: