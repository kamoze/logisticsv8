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

from openerp import models, fields, api, osv, _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class account_invoice(models.Model):
    _inherit = "account.invoice"

    is_parking = fields.Boolean('Parking', readonly=True)
    money_transfer_id = fields.Many2one('fleet.money.transfer', 'From Money Transfer')
    parking_pass_id = fields.Many2one('parking.pass', string='Parking Pass')
    vehicle_book_id = fields.Many2one('fleet.vehicle.booking', "Vehicle Booking")
    trip_book_id = fields.Many2one('fleet.trip.reservation', "Trip Booking")
    package_id = fields.Many2one('fleet.package', "Package Reference")
    goods_info_lines = fields.One2many('package.goods.info', 'invoice_id', string="Goods Information")
    is_luggage = fields.Boolean(string="Luggage Invoice")
    pass_start_date = fields.Date(string="Pass Start Date")
    pass_end_date = fields.Date(string="Pass End Date")

    @api.model
    def create(self, values):
        id = super(account_invoice, self).create(values)
        return id


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    # To change state of money transfer on change of invoice state
    @api.one
    def button_proforma_voucher(self):
        state = ''
        money_transfer_obj = self.env['fleet.money.transfer']
        packaging_obj = self.env['fleet.package']
        fleet_trip_reservation_obj = self.env['fleet.trip.reservation']
        res = super(account_voucher, self).button_proforma_voucher()
        if self._context.get('active_id'):
            account_invoice_brw = self.env['account.invoice'].browse(self._context['active_id'])
            fleet_trip_invoice_id = ''
            money_trans_ids = ''
            package_id = ''
            if account_invoice_brw.type == 'out_invoice':
                fleet_trip_invoice_id = fleet_trip_reservation_obj.search([('invoice_id', '=', self._context['active_id'])])
                money_trans_ids = money_transfer_obj.search([('invoice_id', '=', self._context['active_id'])])
                state = 'receive'
                package_id = packaging_obj.search([('invoice_id', '=', self._context['active_id'])])

            if package_id:
                template_id = self.env.ref('spantree_logistics.spantree_logistics_email_package_trans_send_paid_invoice_template', False)
                if template_id:
                    template_obj = self.pool.get('email.template')
                    template_obj.send_mail(self._cr , self._uid, template_id.id, self._context['active_id'], True, context=None)
                    ctx = dict(self._context)
                    ctx.update({'from_regi_payment': True})
                    packaging_obj.with_context(ctx).send_sms(package_id)

            if account_invoice_brw.type == 'out_refund':
                money_trans_ids = money_transfer_obj.search([('refund_id', '=', self._context['active_id'])])
                state = 'paid'

            if money_trans_ids:
                money_transfer_obj.write(money_trans_ids, {'state': state})
            if fleet_trip_invoice_id:
                customer_seat = []
                customer_return_seat = []
                for seat_id in fleet_trip_invoice_id.seat_ids:
                    if seat_id.trip_id.id == fleet_trip_invoice_id.trip_id.id:
                        customer_seat.append(seat_id.seat_no.id)
                    elif seat_id.trip_id.id == fleet_trip_invoice_id.return_trip_id.id:
                        customer_return_seat.append(seat_id.seat_no.id)
                #if customer_seat:
                #    booked_tickets = fleet_trip_reservation_obj.find_routewise_seats(fleet_trip_invoice_id.source_id.id, fleet_trip_invoice_id.dest_id.id, fleet_trip_invoice_id.trip_id.id)
                #    if list(set(customer_seat) - set(list(set(customer_seat) - set(booked_tickets.get('used_seats'))))):
                #        seat_nos = list(set(customer_seat) - set(list(set(customer_seat) - set(booked_tickets.get('used_seats')))))
                #        seat_list = [str(x.name) for x in self.env['fleet.vehicle.seat'].browse(seat_nos)]
                #        raise Warning(_("Oops ! The seat no(s) %s you are trying to book is already booked. Please change the seat no.") % (seat_list))
                #if customer_return_seat:
                #    booked_tickets = fleet_trip_reservation_obj.find_routewise_seats(fleet_trip_invoice_id.dest_id.id, fleet_trip_invoice_id.source_id.id, fleet_trip_invoice_id.return_trip_id.id)
                #    if list(set(customer_return_seat) - set(list(set(customer_return_seat) - set(booked_tickets.get('used_seats'))))):
                #        seat_nos = list(set(customer_return_seat) - set(list(set(customer_return_seat) - set(booked_tickets.get('used_seats')))))
                #        seat_list = [str(x.name) for x in self.env['fleet.vehicle.seat'].browse(seat_nos)]
                #        raise Warning(_("Oops ! The seat no(s) %s for return ticket(s) you are trying to book is already booked. Please change the seat no.") % (seat_list))
                fleet_trip_invoice_id.write({'state': 'confirmed'})
                template_id = self.env.ref('spantree_logistics.spantree_logistics_email_send_tickets_template', False)
                if template_id:
                    template_obj = self.pool.get('email.template')
                    template_obj.send_mail(self._cr , self._uid, template_id.id, fleet_trip_invoice_id.id, True, context=None)
                ctx = dict(self._context)
                ctx.update({'from_regi_payment': True})
                fleet_trip_invoice_id.with_context(ctx).send_sms(fleet_trip_invoice_id)
        return res


class package_goods_info(models.Model):
    _name = 'package.goods.info'

    goods_name = fields.Char(string="Goods Name")
    goods_description = fields.Text(string="Goods Description")
    goods_qty = fields.Float(string="Goods Quantity")
    goods_price = fields.Float(string="Goods Price")
    invoice_id = fields.Many2one('account.invoice', string="Invoice id")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
