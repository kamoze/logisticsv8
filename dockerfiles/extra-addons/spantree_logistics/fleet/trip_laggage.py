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
from openerp.exceptions import Warning
from datetime import datetime, date
from openerp.exceptions import Warning, RedirectWarning


class luggage_fare(models.Model):
    _name = 'luggage.fare'

    @api.one
    @api.constrains('rate')
    def check_rate(self):
        if self.rate and self.rate < 0.0:
            raise Warning(_('Luggage rate can not zero(0).'))

    source_id = fields.Many2one('fleet.city', string="Source Location", required=True)
    dest_id = fields.Many2one('fleet.city', string="Destination Location", required=True)
    rate = fields.Float(string="Rate", required=True)


class trip_luggage(models.Model):
    _name = "trip.luggage"

    @api.model
    def default_get(self, fields):
        res = super(trip_luggage, self).default_get(fields)
        res.update({'destination_id': self._context.get('dest_id'),
                    'source_id': self._context.get('source_id'),
                    'passenger_id': self._context.get('passenger_id'),
                    'trip_id': self._context.get('trip_id')})
        return res

    @api.one
    @api.depends('charge', 'weight', 'rate')
    def get_total_charges(self):
        if self.charge == 'fixed':
            luggage_fare = self.env['luggage.fare'].search([('source_id', '=', self.source_id.id), ('dest_id', '=', self.destination_id.id)])
            if not luggage_fare:
                model, action_id = self.env['ir.model.data'].get_object_reference('spantree_logistics', 'action_luggage_fare')
                msg = _('Oops !, No Luggage Fare set for Source city %s to Dest. City %s ' \
                                % (self.source_id.name, self.destination_id.name))
                raise RedirectWarning(msg, action_id, _('Go to the Fare Settings'))
            self.total = luggage_fare.rate
        else:
            self.total = self.weight * self.rate
#         return 1.0

    @api.multi
    def make_payment(self):
        if self.invoice_id:
            raise Warning(_("Invoice is already created."))
        if self.reservation_id and self._context.get('from_trip_luggage'):
            vals = {}
            account_invoice_obj = self.env['account.invoice']
            account_invoice_line_obj = self.env['account.invoice.line']
            journal_id = account_invoice_obj._default_journal()
            currency_id = account_invoice_obj._default_currency()
            partner_brw = self.passenger_id or self.env['ir.model.data'].get_object_reference(
                'spantree_logistics', 'res_partner_parking')[1]
            partner_onchange = account_invoice_obj.onchange_partner_id(
                type='out_invoice', partner_id=partner_brw.id)
            product_brw = self.env['product.product'].browse(self.env['ir.model.data'].get_object_reference('spantree_logistics', 'product_luggage_qty_product')[1])
    
            product_onchange = account_invoice_line_obj.product_id_change(product_brw.id, product_brw.uom_id.id,
                                                                          qty=0, name='', type='out_invoice', partner_id=partner_brw.id)
            product_vals = {
                'account_analytic_id': False,
                'account_id': product_onchange['value'] and product_onchange['value']['account_id'] or False,
                'discount': 0,
                'invoice_line_tax_id': [[6, False, []]],
                'name': self.luggage_name or product_brw.name,
                'price_unit': self.total,
                'product_id': product_brw.id,
                'quantity': 1,
                'uos_id': product_brw.uom_id.id
            }
            vals.update({
                'partner_id': partner_brw.id,
                'name': partner_brw.name or False,
                'fiscal_position': partner_onchange['value']['fiscal_position'] and partner_onchange['value']['fiscal_position'] or False,
                'journal_id': journal_id and journal_id.id or False,
                'account_id': partner_onchange['value']['account_id'] and partner_onchange['value']['account_id'] or False,
                'currency_id': currency_id and currency_id.id or False,
                'company_id': self.env['res.company']._company_default_get('account.invoice'),
                'invoice_line': [(0, 0, product_vals)],
                'trip_book_id': self.reservation_id.id,
                'is_luggage': True,
                'payment_term': partner_onchange['value']['payment_term'] and partner_onchange['value']['payment_term'] or False,
            })
            invoice_brw = account_invoice_obj.create(vals)
            self.write({'invoice_id': invoice_brw.id})
            invoice_brw.signal_workflow('invoice_open')
            return self.sudo().make_invoice_paid(invoice_brw.id)

    @api.multi
    def make_invoice_paid(self, invoice_ids):
        '''this is the method which make the invoice paid'''
        if invoice_ids:
            vals_acc_voucher = {}
            user_record = self.env['res.users'].browse([self._uid])
            account_voucher_obj = self.env['account.voucher']
            invoice_brw = self.env['account.invoice'].browse(invoice_ids)
            journal_id = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', user_record.company_id.id)], limit=1)
            all_fields = account_voucher_obj.fields_get([])
            default_get_invoice_payment = account_voucher_obj.with_context({'journal_id':journal_id.id}).default_get(all_fields.keys())
            if self.passenger_id and self.passenger_id.parent_id:
                customer_id = self.passenger_id.parent_id
            else:
                customer_id = self.passenger_id
            res_onchange_journal_id = account_voucher_obj.onchange_journal(
                                                                    journal_id=journal_id.id,
                                                                    line_ids=[(6, 0, [])],
                                                                    tax_id=[],
                                                                    partner_id=customer_id.id,
                                                                    date=date.today(),
                                                                    amount=self.total,
                                                                    ttype='sale',
                                                                    company_id=customer_id.company_id.id,
                                                                )
            res_onchange_amount = account_voucher_obj.onchange_amount(
                                                        amount=self.total,
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
            self.do_manifest()
        return True

    @api.multi
    def do_manifest(self):
        if self:
            trip_board_pass_obj = self.env['trip.board.passenger']
            trip_board_chart_id = trip_board_pass_obj.search([('trip_id', '=', self.trip_id.id)])
            vals = {'reservation_id': self.reservation_id.id,
                    'trip_id': self.trip_id.id,
                    'passenger_id': self.passenger_id.id,
                    'luggage_name': self.luggage_name,
                    'source_id': self.source_id.id,
                    'destination_id': self.destination_id.id,
                    'charge': self.charge,
                    'weight': self.weight,
                    'rate': self.rate,
                    'total': self.total,
                    'invoice_id': self.invoice_id.id,
                    'luggage_line_id': self.id}
            if trip_board_chart_id:
                trip_board_chart_id.write({'luggage_ids': [(0, 0, vals)]})
            else:
                trip_board_pass_obj.create({'trip_id': self.trip_id and self.trip_id.id or False,
                                            'employee_id': self.trip_id and self.trip_id.vehicle_id and self.trip_id.vehicle_id.employee_driver_id and self.trip_id.vehicle_id.employee_driver_id.id or False,
                                            'vehicle_id': self.trip_id and self.trip_id.vehicle_id and self.trip_id.vehicle_id.id or False,
                                            'luggage_ids': [(0, 0, vals)]})
        return True

    @api.multi
    def print_invoice(self):
        return self.env['report'].get_action(self.invoice_id, 'account.report_invoice')

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
    total = fields.Float(string="Total", compute="get_total_charges", store=True)
    invoice_id = fields.Many2one('account.invoice', string="Invoice ID")
    seat_id = fields.Many2one('fleet.vehicle.seat', string='Seat No.')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: