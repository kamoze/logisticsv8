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
from datetime import datetime, date
from openerp.exceptions import Warning
from openerp import SUPERUSER_ID


class wizard_trip_board(models.TransientModel):
    _name = 'wizard.trip.board'

    tickets_boards = fields.Text(string="Tickets Boards")

    @api.multi
    def prepare_trip_boarding(self):
        trip_board_pass_obj = self.env['trip.board.passenger']
        trip_seat_obj = self.env['trip.reservation.seat']
        fleet_trip_obj = self.env['fleet.trip']
        trip_board_pass = {}
        for seat_id in set([id for id in self.tickets_boards.split('\n')]):
            if seat_id:
                trip_rev_seat_id = trip_seat_obj.search([('barcode', '=', seat_id)])
                if trip_rev_seat_id:
                    trip_date = datetime.strptime(trip_rev_seat_id.trip_id.start_time, '%Y-%m-%d %H:%M:%S').date()
                    if trip_date < date.today():
                        raise Warning(_("Oops, The booking number %d you are trying to board its corresponding trip %s is already departed.")  % (int(seat_id), trip_rev_seat_id.trip_id.name))
                    trip_board_pass_line_id = self.env['trip.passenger.board.line'].search([('barcode', '=', seat_id)])
                    if trip_board_pass_line_id:
                        continue
                    if trip_board_pass.has_key(trip_rev_seat_id.trip_id.id):
                        seat_data = [0, 0, {'reservation_id': trip_rev_seat_id.reservation_id.id,
                                            'partner_id': trip_rev_seat_id.reservation_id.customer_id.id,
                                            'passenger_type':trip_rev_seat_id.passenger_type.id,
                                            'source_id': trip_rev_seat_id.source_id.id,
                                            'dest_id': trip_rev_seat_id.dest_id.id,
                                            'board_loc_id': trip_rev_seat_id.board_loc_id.id,
                                            'trip_id': trip_rev_seat_id.trip_id.id,
                                            'seat_no': trip_rev_seat_id.seat_no.id,
                                            'price': trip_rev_seat_id.price,
                                            'is_board': True,
                                            'barcode': trip_rev_seat_id.barcode}]
                        (trip_board_pass.get(trip_rev_seat_id.trip_id.id)).append(seat_data)
                        trip_board_pass.update({trip_rev_seat_id.trip_id.id: trip_board_pass.get(trip_rev_seat_id.trip_id.id)})
                    else:
                        seat_data = [0, 0, {'reservation_id': trip_rev_seat_id.reservation_id.id,
                                            'partner_id': trip_rev_seat_id.reservation_id.customer_id.id,
                                            'passenger_type':trip_rev_seat_id.passenger_type.id,
                                            'source_id': trip_rev_seat_id.source_id.id,
                                            'dest_id': trip_rev_seat_id.dest_id.id,
                                            'board_loc_id': trip_rev_seat_id.board_loc_id.id,
                                            'trip_id': trip_rev_seat_id.trip_id.id,
                                            'seat_no': trip_rev_seat_id.seat_no.id,
                                            'price': trip_rev_seat_id.price,
                                            'is_board': True,
                                            'barcode': trip_rev_seat_id.barcode}]
                        trip_board_pass.update({trip_rev_seat_id.trip_id.id: [seat_data]})
        if trip_board_pass:
            for key, value in trip_board_pass.iteritems():
                trip_board_chart_id = trip_board_pass_obj.search([('trip_id', '=', key)])
                if trip_board_chart_id:
                    trip_board_chart_id.write({'reservation_seat_ids': value})
                else:
                    trip_id = fleet_trip_obj.browse(key)
                    trip_board_pass_obj.create({'trip_id':trip_id and trip_id.id or False,
                                                'employee_id': trip_id and trip_id.vehicle_id and trip_id.vehicle_id.employee_driver_id and trip_id.vehicle_id.employee_driver_id.id or False,
                                                'vehicle_id': trip_id and trip_id.vehicle_id and trip_id.vehicle_id.id or False,
                                                'reservation_seat_ids': value})


class trip_passenger_board_line(models.Model):
    _name = 'trip.passenger.board.line'

    @api.multi
    def write(self, vals):
        if self.is_verified:
            raise Warning(_("The record you are trying to edit is verified and now it can not be modified."))
        return super(trip_passenger_board_line, self).write(vals)

    @api.one
    def unlink(self):
        if self.is_verified:
            raise Warning(_("The record you are trying to delete is verified and now it can not be delete."))
        return super(trip_passenger_board_line, self).unlink()

    @api.model
    def default_get(self, fields_list):
        fleet_trip_obj= self.env['fleet.trip']
        res = super(trip_passenger_board_line, self).default_get(fields_list)
        if self._context.get('trip_id'):
            trip_id = fleet_trip_obj.browse(self._context.get('trip_id'))
            res.update({'source_id': trip_id.route_id.city_source.id, 'dest_id': trip_id.route_id.city_destination.id, 'trip_id': trip_id.id})
        return res

    partner_id = fields.Many2one('res.partner', 'Passenger Name')
    passenger_type = fields.Many2one('passenger.type', 'Passenger Type', required=True)
    seat_qty = fields.Integer('No. of Seats', readonly=True, default=1)
    price = fields.Float('Price', store=True)
    reservation_id = fields.Many2one('fleet.trip.reservation', "Reservation", ondelete='cascade')
    seat_no = fields.Many2one('fleet.vehicle.seat', 'Seat No.', required=True)
    trip_id = fields.Many2one('fleet.trip', "Trip")
    source_id = fields.Many2one('fleet.city', 'Source City', readonly=False)
    dest_id = fields.Many2one('fleet.city', 'Dest. City', readonly=False)
    board_loc_id = fields.Many2one('fleet.parking.location', string='Boarding Location')
    no_of_seat = fields.Integer(string="No. of Seat")
    board_chart_id = fields.Many2one('trip.board.passenger', string="Board Chart", ondelete='cascade')
    is_board = fields.Boolean(string="Boarding Status")
    is_verified = fields.Boolean(string="Verified")
    barcode = fields.Char(string="Barcode")


class trip_pass_board_luggage_line(models.Model):
    _name = 'trip.pass.board.luggage.line'
 
    reservation_id = fields.Many2one('fleet.trip.reservation', string="Reservation")
    trip_id = fields.Many2one('fleet.trip', string="Trip")
    passenger_id = fields.Many2one('res.partner', string="Passenger Name")
    luggage_name = fields.Char(string="Luggage Name")
    source_id = fields.Many2one('fleet.city', string="Source City")
    destination_id = fields.Many2one('fleet.city', string="Destination City")
    charge = fields.Selection([('fixed', 'Fixed'), ('weight', 'Weight')],
                              string="Charge", default="fixed")
    weight = fields.Float(string="Weight")
    rate = fields.Float(string="Rate")
    total = fields.Float(string="Total", store=True)
    invoice_id = fields.Many2one('account.invoice', string="Invoice ID")
    luggage_line_id = fields.Many2one('trip.luggage', string="Luggage_line_id")
    board_chart_id = fields.Many2one('trip.board.passenger', string="Manifest ID")


class trip_board_passenger(models.Model):
    _name = 'trip.board.passenger'

    trip_id = fields.Many2one('fleet.trip', string="Trip")
    reservation_seat_ids = fields.One2many('trip.passenger.board.line', 'board_chart_id', string="Passenger List")
    state = fields.Selection([('new', 'New'), ('verified', 'Verified'), ('closed', 'Closed')], string="State", default='new')
    employee_id = fields.Many2one('hr.employee', string="Driver")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    luggage_ids = fields.One2many('trip.pass.board.luggage.line', 'board_chart_id', string="Luggage Details", copy=False)

    @api.one
    def verify(self):
        if self.reservation_seat_ids:
            for line_id in self.reservation_seat_ids:
                if line_id:
                    line_id.write({'is_verified': True})
                    template_obj = self.pool.get('email.template')
                    template_id = template_obj.browse(self._cr, self._uid, self.pool.get('ir.model.data').get_object_reference(self._cr, self._uid, 'spantree_logistics', 'email_template_trip_passenger_wishing')[1])
                    if template_id:
                        template_obj.send_mail(self._cr, self._uid, template_id.id, line_id.id, True, context=None)
                    ticket_code = str(line_id.reservation_id.name) + str(line_id.trip_id.id).rjust(3, '0') + str(line_id.seat_no.id).rjust(2, '0')
                    message = "Dear " + line_id.partner_id.name + ",Wishing You Happy and Safe Journey.,Ticket info.,Trip: " + line_id.trip_id.name + ",Ticket Code: " + ticket_code
                    if line_id.partner_id.mobile and message:
                        self.env['sms.config'].send_sms(int(line_id.partner_id.mobile), message)
            self.write({'state': 'verified'})
        return True

    @api.one
    def close(self):
        template_obj = self.pool.get('email.template')
        template_id = template_obj.browse(self._cr, self._uid, self.pool.get('ir.model.data').get_object_reference(self._cr, self._uid, 'spantree_logistics', 'email_template_trip_boarding_manifest_close')[1])
        if template_id:
            template_obj.send_mail(self._cr, self._uid, template_id.id, self.id, True, context=None)
            self.write({'state': 'closed'})
        return True

    @api.multi
    def get_admin_email(self):
        return self.env['res.users'].browse(SUPERUSER_ID).email

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: