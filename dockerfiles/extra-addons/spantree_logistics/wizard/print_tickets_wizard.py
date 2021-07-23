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

from openerp.exceptions import Warning
from openerp import fields, models, api, _


class print_tickets_wizard(models.TransientModel):
    _name = 'print.tickets.wizard'

    booking_no = fields.Char(string="Booking Number")
    pin_no = fields.Char(string="Pin")

    @api.multi
    def get_tickets(self):
        trip_reservation_id = self.env['fleet.trip.reservation'].sudo().search([('name', '=', self.booking_no)])
        if not trip_reservation_id:
            raise Warning(_("Oops, No booking found with this (%s) number.") % (self.booking_no))
        if trip_reservation_id.customer_id.sudo().pin_no:
            if trip_reservation_id and trip_reservation_id.customer_id.sudo().pin_no != self.pin_no:
                raise Warning(_("Oops, Pin number is wrong."))
        self.booking_no = False
        self.pin_no = False
        return self.env['report'].sudo().get_action(trip_reservation_id, 'spantree_logistics.report_ticket_temp')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: