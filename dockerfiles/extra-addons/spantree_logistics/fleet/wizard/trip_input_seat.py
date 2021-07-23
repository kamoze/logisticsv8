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


class trip_input_seat(models.Model):
    _name = "trip.input.seat"

    passenger_type = fields.Many2one('passenger.type', 'Passenger Type', required=True,)
    no_of_seat = fields.Integer('No. of Seats', default=1)
    total_seats = fields.Many2many('fleet.vehicle.seat', 'trip_booked_seats', 'trip_input_id', 'trip_seat_id')

    @api.model
    def default_get(self, fields):
        trip_seat = []
        res = super(trip_input_seat, self).default_get(fields)
        fleet_trip_res = self.env['fleet.trip.reservation']
        fleet_seat = self.env['fleet.vehicle.seat']
        model, type_id = self.env['ir.model.data'].get_object_reference('spantree_logistics', 'passenger_type_adult')
        res.update({'passenger_type': type_id or False})
        if self._context.get('active_id'):
            res_data = fleet_trip_res.search([('id', '=', [self._context.get('active_id')])])
            seats_data = fleet_trip_res.find_routewise_seats(res_data.source_id.id, res_data.dest_id.id,res_data.trip_id.id)
            if seats_data:
                seat_id = fleet_seat.search([('id', 'in', seats_data.get('used_seats'))])
                trip_seat = [x.id for x in seat_id]
        res.update({'total_seats' : [(6, 0, trip_seat)]})
        return res

    @api.one
    def reserve_seats(self):
        created_lines = []
        passenger_type = self.passenger_type
        no_of_seat = self.no_of_seat
        mega_list = []
        price = 0.0
        trip_res = self.env['fleet.trip.reservation']
        trip_seat = self.env['trip.reservation.seat']
        trip_fare = self.env['trip.config.fare']
        trip_reservation = trip_res.browse(self._context.get('active_ids')[0])
        total_price = 0.0
        seats_data = self.env['fleet.trip.reservation'].sudo().find_routewise_seats(trip_reservation.source_id.id, trip_reservation.dest_id.id, trip_reservation.trip_id.id,)
        if not seats_data.get('free_seats'):
            raise Warning(_('Oops !, No Seats Left'))

        if len(seats_data.get('free_seats')) < no_of_seat:
            raise except_orm(_('Not Enough Tickets'), _('Oops !, Only %d Seats Left in %s') \
                             % (len(seats_data.get('free_seats')), trip_reservation.trip_id.name))

        # find fare for above passenger type

        fare = trip_fare.search([('route_id', '=', trip_reservation.trip_id.route_id.id)])
        if not fare:
            raise Warning(_('Oops !, No trip fare is define..!!'))
        if fare:
            if not trip_reservation.return_trip:
                for all_fares in fare.fare_lines:
                    if all_fares.from_city == trip_reservation.source_id and all_fares.to_city == trip_reservation.dest_id and not all_fares.round_trip:
                        for ptype in all_fares.passenger_types:
                            if ptype == passenger_type:
                                price = all_fares.price
                if not price :
                    model, action_id = self.env['ir.model.data'].get_object_reference('spantree_logistics', 'trip_config_fare_act')
                    msg = _('Oops !, No Fare set for this Passenger type for Source city %s and Dest. City %s in Route %s' \
                            % (trip_reservation.source_id.name, trip_reservation.dest_id.name, trip_reservation.trip_id.route_id.name))
                    raise RedirectWarning(msg, action_id, _('Go to the Fare Settings'))

#                 raise Warning(_('Oops !, No Fare set for this Passenger type for Source city %s and Dest. City %s in Route %s' \
#                                 % (trip_reservation.source_id.name, trip_reservation.dest_id.name, trip_reservation.trip_id.route_id.name)))
            for each_seat in range(1, no_of_seat + 1):
                seat_no = seats_data.get('free_seats')[each_seat - 1]
                mega_list.append({'passenger_type': passenger_type.id,
                                  'seat_qty': 1,
                                  'price': price,
                                  'seat_no': seats_data.get('free_seats')[each_seat - 1],
                                  'reservation_id': trip_reservation.id,
                                  'trip_id': trip_reservation.trip_id.id,
                                  'source_id': trip_reservation.source_id.id,
                                  'dest_id': trip_reservation.dest_id.id,
                                  'name': trip_reservation.customer_id.name,
                                  'board_loc_id' : trip_reservation.parking_loc_id.id,
                                  'barcode': str(trip_reservation.name) + str(trip_reservation.trip_id.id).rjust(3, '0') + str(seat_no).rjust(2, '0')
                                  })
            if not trip_reservation.return_trip:
                for line in mega_list:
                    trip_id = trip_seat.create(line)
                    created_lines.append(trip_id)
                for seat in trip_reservation.seat_ids:
                    total_price += seat.price
                trip_reservation.total_price = total_price

# RETURN TRIP LINE
        if trip_reservation.return_trip:
            if trip_reservation.return_trip_id and trip_reservation.return_date:
                mega_list_return = []
                price = 0.0
                total_price = 0.0
                seats_data = self.env['fleet.trip.reservation'].find_routewise_seats(trip_reservation.dest_id.id, trip_reservation.source_id.id, trip_reservation.return_trip_id.id,)
                if not seats_data.get('free_seats'):
                    raise Warning(_('Oops !, No Seats Left'))

                if len(seats_data.get('free_seats')) < no_of_seat:
                    raise except_orm(_('Not Enough Tickets for Return Trip'), _('Oops !, Only %d Seats Left in %s') \
                                     % (len(seats_data.get('free_seats')), trip_reservation.return_trip_id.name))

                for each_seat in range(1, no_of_seat + 1):
                    seat_no = seats_data.get('free_seats')[each_seat - 1]
                    mega_list_return.append({'passenger_type': passenger_type.id,
                                              'seat_qty': 1,
                                              'price': 0,  # price gets filled by compute fields
                                              'seat_no': seat_no,
                                              'reservation_id': trip_reservation.id,
                                              'trip_id': trip_reservation.return_trip_id.id,
                                              'source_id': trip_reservation.dest_id.id,
                                              'dest_id': trip_reservation.source_id.id,
                                              'name': trip_reservation.customer_id.name,
                                              'board_loc_id' : trip_reservation.return_park_loc_id.id,
                                              'barcode': str(trip_reservation.name) + str(trip_reservation.return_trip_id.id).rjust(3, '0') + str(seat_no).rjust(2, '0')
                                             })
                for line in mega_list_return:
                    trip_id = trip_seat.create(line)
                    created_lines.append(trip_id)
            for line in mega_list:
                line.update({'price': 0.0})  # price gets filled by compute fields
                trip_id = trip_seat.create(line)
                created_lines.append(trip_id)
            # Total for trip.res
            for seat in trip_reservation.seat_ids:
                total_price += seat.price
            trip_reservation.total_price = total_price
        return created_lines

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: