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
from openerp import SUPERUSER_ID
from openerp.exceptions import except_orm, Warning, RedirectWarning


class config_setting_transport(models.Model):
    _name = 'config.setting.transport'

    seat_nos = fields.Integer('Generic Seats',)

    @api.one
    def execute(self,):
        return True

    @api.model
    def default_get(self, fields):
        res = super(config_setting_transport, self).default_get(fields)
        ids = self.search([])
        if len(ids):
            last_id = ids[-1]
            res.update({'seat_nos': last_id.seat_nos, })
        return res

    @api.model
    def create(self, vals):
        if vals.get('seat_nos') and int(vals.get('seat_nos')) < 0:
            raise Warning(_('No. of seats for vehicle can not be negative.'))
        # The below code to create/update seat records for seat qty given in settings page
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        vehicle_seat = self.env['fleet.vehicle.seat']
        all_ids = self.search([])
        if all_ids:
            last_id = all_ids[-1]
            if last_id and len(last_id) > 0 and last_id.seat_nos < vals.get('seat_nos'):
                # new seats greater than old one
                seats_config = vehicle_seat.search([('vehicle_id', '=', False)])
                if seats_config:
                    last_seat_no = seats_config[-1].seat_no
                    if last_seat_no.isdigit():
                        for seat in range(int(last_seat_no) + 1, vals.get('seat_nos') + 1):
                            vehicle_seat.create({'seat_no': str(seat)})
            all_ids.unlink()
        else:
#             don't know why, but even after giving value for seat amount in settings page, sometimes it asked for seat qty again
            seats_config = vehicle_seat.search([('vehicle_id', '=', False)])
            if seats_config:
                last_seat_no = seats_config[-1].seat_no
                if last_seat_no.isdigit():
                    for seat in range(int(last_seat_no) + 1, vals.get('seat_nos') + 1):
                        vehicle_seat.create({'seat_no': str(seat)})
            else:
                for seat in range(1, vals.get('seat_nos') + 1):
                    vehicle_seat.create({'seat_no': str(seat)})
        res = super(config_setting_transport, self).create(vals)
        return res

    @api.multi
    def write(self, vals, context={}):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        if vals.get('seat_nos') and int(vals.get('seat_nos')) < 0:
            raise Warning(_('No. of seats for vehicle can not be negative.'))
        vehicle_seat = self.env['fleet.vehicle.seat']
        if vals.get('seat_nos'):
            if vals.get('seat_nos') > self.seat_nos:
                seats_config = vehicle_seat.search([('vehicle_id', '=', False)])
                if seats_config:
                    last_seat_no = seats_config[-1].seat_no
                    if last_seat_no.isdigit():
                        for seat in range(int(last_seat_no) + 1, vals.get('seat_nos') + 1):
                            vehicle_seat.create({'seat_no': str(seat)})
                else:
                    for seat in range(1, vals.get('seat_nos') + 1):
                        vehicle_seat.create({'seat_no': str(seat)})
        res = super(config_setting_transport, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(config_setting_transport, self).unlink()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: