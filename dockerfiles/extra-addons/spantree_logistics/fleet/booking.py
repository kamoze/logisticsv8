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
from datetime import datetime, timedelta,date
from openerp.exceptions import Warning


class vehicle_booking_fare(models.Model):
    _name = 'vehicle.booking.fare'

    @api.one
    @api.constrains('day_price', 'hour_price', 'week_price', 'fixed_price')
    def check_rate(self):
        if (self.day_price and self.day_price < 0.0) or (self.hour_price and self.hour_price < 0.0)\
            or (self.week_price and self.week_price < 0.0) or (self.fixed_price and self.fixed_price < 0.0):
            raise Warning(_('Vehicle booking changes can not zero(0).'))

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    day_price = fields.Float(string="Price Per Day")
    hour_price = fields.Float(string="Price Per Hour")
    week_price = fields.Float(string="Price Per Week")
    fixed_price = fields.Float(string="Fixed Price")


class booking_document(models.Model):
    _name = 'booking.document'

    name = fields.Char(string='Name')
    document = fields.Binary(string='Document')
    booking_id = fields.Many2one('fleet.vehicle.booking', 'Booking')


class fleet_vehicle_booking(models.Model):
    _name = 'fleet.vehicle.booking'
    _rec_name = 'number'

    @api.multi
    def action_print_invoice(self):
        return self.env['report'].get_action(self.invoice_id, 'account.report_invoice')

    @api.one
    @api.depends('start_date', 'end_date')
    def _calculate_days(self):
        if self.start_date and self.end_date:
            start_date_f = datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')
            rounded_start = start_date_f.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date_f = datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S')
            rounded_end = end_date_f.replace(hour=0, minute=0, second=0, microsecond=0)
            self.trip_days = (rounded_end - rounded_start).days + 1
            self.trip_hours = ((datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S')  - datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S')).total_seconds())/3600
            weeks = ((datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S') - datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S'))).days
            if weeks:
                if weeks%7 == 0:
                    self.trip_weeks = weeks/7
        return True

    @api.multi
    @api.depends('state')
    def _get_is_invoiced(self):
        if self.id:
            invoice_ids = self.env['account.invoice'].search([('vehicle_book_id', '=', self.id)])
            if invoice_ids:
                self.write({'is_invoiced': True})
                self.is_invoiced = True

    @api.multi
    @api.onchange('amount_based_on')
    def onchange_amount_based_on(self):
        if self.amount_based_on and not self.vehicle_id:
            raise Warning(_('Select vehicle first!'))
        if self.vehicle_id:
            fare_id = self.env['vehicle.booking.fare'].search([('vehicle_id', '=', self.vehicle_id.id)])
            if not fare_id:
                raise Warning(_('Please make the configuration for %s vehicle' %self.vehicle_id.name))
            if self.amount_based_on:
                if self.amount_based_on == 'fixed':
                    self.fixed_charge = fare_id.fixed_price
                if self.amount_based_on == 'days':
                    self.charge_per_day = fare_id.day_price
                if self.amount_based_on == 'hours':
                    self.charge_per_hour = fare_id.hour_price
                if self.amount_based_on == 'weeks' and self.trip_weeks != 0:
                    self.charge_per_week = fare_id.week_price

    @api.one
    @api.depends('amount_based_on', 'fixed_charge', 'charge_per_day', 'trip_days', 'extra_amt')
    def _calculate_amount(self):
        if self.fixed_charge and self.amount_based_on and self.amount_based_on == 'fixed':
            self.final_price = self.fixed_charge
        if self.charge_per_day and self.amount_based_on and self.amount_based_on == 'days':
            self.final_price = self.charge_per_day * self.trip_days
        if self.charge_per_hour and self.amount_based_on and self.amount_based_on == 'hours':
            self.final_price = self.charge_per_hour * self.trip_hours
        if self.charge_per_week and self.amount_based_on and self.amount_based_on == 'weeks':
            self.final_price = self.charge_per_week * self.trip_weeks
        if self.extra_amt:
            self.final_price += self.extra_amt
        return True

    customer_id = fields.Many2one('res.partner', "Customer", required=True)
    number = fields.Char('Number', readonly=True)
    start_date = fields.Datetime('Start Date', required=True)
    end_date = fields.Datetime('End Date', required=True)
    amount_based_on = fields.Selection([('fixed', 'Fixed'), ('days', 'Days'),
                                        ('hours', 'Hours'), ('weeks', 'Weeks')],
                                       'Amount based on', required=True)
    fixed_charge = fields.Float('Fixed Charge')
    charge_per_day = fields.Float('Per Day Charge')
    charge_per_hour = fields.Float('Per Hour Charge')
    charge_per_week = fields.Float('Per Week Charge')
    trip_days = fields.Integer('Trip Days', readonly=True, compute=_calculate_days)
    trip_hours = fields.Float(string="Trip Hours", compute=_calculate_days)
    trip_weeks = fields.Integer(string="Trip Week", compute=_calculate_days)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)
    start_city = fields.Many2one('fleet.city', 'Start Location', required=True)
    end_city = fields.Many2one('fleet.city', 'End Location', required=True)
    final_price = fields.Float('Final Amount', readonly=True, compute=_calculate_amount)
    note = fields.Text('Note')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('in_progress', 'In Progress'), ('cancelled', 'Cancelled'),
                              ('done', 'Done')], default='draft')
    document_ids = fields.One2many('booking.document', 'booking_id', 'Documents')
    reason_cancel = fields.Text('Reason for Cancelling')
    extra_amt = fields.Float('Misellaneous Amount')
    is_invoiced = fields.Boolean(string="Is Invoiced", compute=_get_is_invoiced)
    penalties_lines = fields.One2many('penalties.lines', 'booking_id', string="Penalties Lines")
    invoice_id = fields.Many2one('account.invoice', string="Invoice")

    @api.multi
    def make_payment(self, penalty_line_id=None, booking_id=None, amt=None):
        if self._context.get('from_penalties_lines') and penalty_line_id:
            custo_id = booking_id.customer_id
            penalty_line_brw_id = self.env['penalties.lines'].browse(penalty_line_id)
            prod_id = penalty_line_brw_id.product_id.id
            prod_description = penalty_line_brw_id.name
        else:
            custo_id = self.customer_id
            amt = self.final_price
            prod_id = self.env['ir.model.data'].get_object_reference('spantree_logistics',
                                                                       'booking_charges_product')[1]

        vals = {}
        account_invoice_obj = self.env['account.invoice']
        cust_id = custo_id or self.env['ir.model.data'].get_object_reference('spantree_logistics', 'res_partner_vehicle_booking')[1]
        res_partner = account_invoice_obj.onchange_partner_id('out_invoice', partner_id=cust_id.id)
        booking_charge_id = prod_id
        booking_charge_prod_id = self.env['product.product'].browse(booking_charge_id)
        product_booking_charge = self.env['account.invoice.line'].product_id_change(booking_charge_id,
                                                                            booking_charge_prod_id.uom_id.id,
                                                                            qty=0, name='',
                                                                            type='out_invoice',
                                                                            partner_id=cust_id.id)
        if not product_booking_charge['value'].get('account_id'):
            account_id = self.env['ir.property'].get('property_account_income_categ', 'product.category')
            if account_id:
                account_id = account_id.id
        else:
            account_id = product_booking_charge['value']['account_id']
        if not product_booking_charge['value'].get('name'):
            prod_description = penalty_line_brw_id.name
        else:
            prod_description = product_booking_charge['value']['name']
        booking_charge_vals = {
            'account_analytic_id': False,
            'account_id': account_id or False,
            'discount': 0,
            'invoice_line_tax_id': [[6, False, []]],
            'name': prod_description or False,
            'price_unit': amt and amt or False,
            'product_id': booking_charge_id and booking_charge_id or False,
            'quantity': 1,
            'uos_id': booking_charge_prod_id.uom_id and booking_charge_prod_id.uom_id.id or False
        }
        vals.update({
            'partner_id': cust_id.id or False,
            'fiscal_position': res_partner['value']['fiscal_position'] and res_partner['value']['fiscal_position'] or False,
            'journal_id': account_invoice_obj._default_journal() and (account_invoice_obj._default_journal()).id or False,
            'account_id': res_partner['value']['account_id'] and res_partner['value']['account_id'] or False,
            'currency_id': account_invoice_obj._default_currency() and (account_invoice_obj._default_currency()).id or False,
            'company_id': self.env['res.company']._company_default_get('account.invoice'),
            'invoice_line': booking_charge_vals and [(0, 0, booking_charge_vals)] or False,
            'vehicle_book_id': self.id or booking_id.id,
        })
        invoice_brw = account_invoice_obj.create(vals)
        # To change state of invoice to open state
        invoice_brw.signal_workflow('invoice_open')
        self.write({'invoice_id':invoice_brw.id})
#        To change the state of invoice to done state use following method
#         self.env['fleet.trip.reservation'].paid_invoice2(invoice_brw.id)
        return invoice_brw.id

    @api.one
    def start_booking(self):
        self.write({'state': 'in_progress'})
        return True

    @api.one
    def action_confirm(self):
        self.write({'state': 'confirmed'})
        return True

    @api.one
    def action_done(self):
        self.write({'state': 'done'})
        return True

    @api.one
    def create_refund(self):
        account_bank_statement_line_obj = self.env['account.bank.statement.line']
        account_bank_statement_obj_id = self.env['account.bank.statement'].search([('user_id','=',self._uid),('date','=',date.today().strftime('%Y-%m-%d')),('state', '=', 'open')])
        if not account_bank_statement_obj_id:
            raise except_orm(_('Cash Register Not Found'), 
                             ('please contact to admin to create cash register'))
        account_bank_statement_line_obj.create({'date': self.start_date,
                                               'name': 'Vehicle' + '/' + self.number,
                                               'amount': -self.final_price,
                                               'statement_id': account_bank_statement_obj_id.id,
                                               'ref': self.vehicle_id.name,
                                               'partner_id': self.customer_id.id,
                                               })
        return self.write({'state': 'cancelled'})
#         return True
#         vals = {}
#         account_invoice_obj = self.env['account.invoice']
#         cust_id = self.env['ir.model.data'].get_object_reference('transport_management', 'res_partner_money_transfer')[1]
#         res_partner = account_invoice_obj.onchange_partner_id('out_refund', cust_id)
#         money_tran_id = self.env['ir.model.data'].get_object_reference('transport_management',
#                                                                        'product_product_money_transfer')[1]
#         money_tran_brw = self.env['product.product'].browse(money_tran_id)
#         product_money_transfer = self.env['account.invoice.line'].product_id_change(money_tran_id,
#                                                                             money_tran_brw.uom_id.id,
#                                                                             qty=0, name='',
#                                                                             type='out_refund',
#                                                                             partner_id=cust_id)
#         money_transfer_vals = {
#             'account_analytic_id': False,
#             'account_id': product_money_transfer['value'] and product_money_transfer['value']['account_id'] or False,
#             'discount': 0,
#             'invoice_line_tax_id': [[6, False, []]],
#             'name': product_money_transfer['value'] and product_money_transfer['value']['name'] or False,
#             'price_unit': self.final_price and self.final_price or False,
#             'product_id': money_tran_id and money_tran_id or False,
#             'quantity': 1,
#             'uos_id': money_tran_brw.uom_id and money_tran_brw.uom_id.id or False
#         }
#         vals.update({
#             'partner_id': cust_id and cust_id or False,
#             'fiscal_position': res_partner['value']['fiscal_position'] and res_partner['value']['fiscal_position'] or False,
#             'journal_id': account_invoice_obj._default_journal() and (account_invoice_obj._default_journal()).id or False,
#             'account_id': res_partner['value']['account_id'] and res_partner['value']['account_id'] or False,
#             'currency_id': account_invoice_obj._default_currency() and (account_invoice_obj._default_currency()).id or False,
#             'company_id': self.env['res.company']._company_default_get('account.invoice'),
#             'invoice_line': money_transfer_vals and [(0, 0, money_transfer_vals)] or False,
#             'vehicle_book_id': self.id,
#             'type': 'out_refund',
#         })
#         refund_id = account_invoice_obj.create(vals)
#         self.env['fleet.trip.reservation'].paid_invoice2(refund_id.id)
#         return self.write({'state': 'cancelled', })

    @api.one
    def action_cancel(self):
        self.state = 'cancelled'
        return True

#     @api.v7
#     def action_view_invoice(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'invoice_form')[1]
#         return {
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'account.invoice',
#             'view_id': [view_id],
#             'res_id': self.browse(cr, uid, ids, context=context).invoice_id.id,
#             'type': 'ir.actions.act_window',
#         }

    @api.model
    def create(self, vals):
        vehicles = self.env['fleet.vehicle'].check_vehicle_overlap(vals.get('start_date'), vals.get('end_date'))
        #if not vehicles:
        #    raise Warning(_("Selected Vehicle is not available for selected date(s)."))
        #if vals.get('vehicle_id') not in [vehicle[0] for vehicle in vehicles]:
         #   raise Warning(_("Selected Vehicle ID is not available for selected date(s)."))
        if vals.get('amount_based_on') == 'weeks' and vals.get('trip_weeks') == 0:
            raise Warning(_('No. of weeks are zero(0).so the charges can not be calculated.'))
        vals['number'] = self.env['ir.sequence'].get('vehicle_booking')
        vals.update({'parking_user': self._uid})
        ret_val = super(fleet_vehicle_booking, self).create(vals)
        return ret_val

    @api.multi
    def write(self, vals):
        amount_based_on = vals.get('amount_based_on') if vals.get('amount_based_on') else self.amount_based_on or ''
        trip_weeks = vals.get('trip_weeks') if vals.get('trip_weeks') else self.trip_weeks or 0
        if amount_based_on == 'weeks' and trip_weeks == 0:
            raise Warning(_('No. of weeks are zero(0).so the charges can not be calculated.'))
        return super(fleet_vehicle_booking, self).write(vals)


class penalties_lines(models.Model):
    _name = 'penalties.lines'

    @api.multi
    def make_payment(self):
        if self.invoice_id:
            raise Warning(_("Invoice is already created."))
        if self.booking_id and self._context.get('from_penalties_lines'):
            invoice_id = self.env['fleet.vehicle.booking'].make_payment(self.id, self.booking_id, self.amount)
            if invoice_id:
                self.write({'invoice_id': invoice_id})

    @api.one
    @api.onchange('product_id')
    def on_change_product_id(self):
        if self.product_id:
            if self.product_id.description_sale:
                self.name = self.product_id.name + ' ' +self.product_id.description_sale
            else:
                self.name = self.product_id.name

    product_id = fields.Many2one('product.product', string="Product")
    name = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount")
    invoice_id = fields.Many2one('account.invoice', string="Invoice ID")
    booking_id = fields.Many2one('fleet.vehicle.booking', string="Booking ID")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
