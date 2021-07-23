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


class booking_payment_wizard(models.TransientModel):
    _name = "booking.payment.wizard"

    @api.one
    @api.depends('amt_invoiced', 'remaining_amt')
    def _compute_charges(self):
        booking = self.env['fleet.vehicle.booking'].browse(self._context['active_id'])
        invoices = self.env['account.invoice'].search([('vehicle_book_id', '=', self._context['active_id']),
                                                       ('state', '=', 'paid')])
        amt_total = 0.0
        if invoices:
            for each_inv in invoices:
                amt_total += each_inv.amount_total
            self.amt_invoiced = amt_total
        self.remaining_amt = booking.final_price - amt_total
        return True

#     create_invoice = fields.Boolean('To Be Invoiced', default=True)

    amt_invoiced = fields.Float('Advance Invoiced',)
    remaining_amt = fields.Float('Amount to Invoice',)
    extra_charge = fields.Float('Extra Charges')

    @api.model
    def default_get(self, fields):
        res = super(booking_payment_wizard, self).default_get(fields)
        booking = self.env['fleet.vehicle.booking'].browse(self._context['active_id'])
        invoices = self.env['account.invoice'].search([('vehicle_book_id', '=', self._context['active_id']),
                                                       ('state', '=', 'paid')])
        amt_total = 0.0
        if invoices:
            for each_inv in invoices:
                amt_total += each_inv.amount_total
#             self.amt_invoiced = amt_total
            res.update({'amt_invoiced':amt_total})
        res.update({'remaining_amt':booking.final_price - amt_total})
        return res

    @api.one
    def create_invoice(self):
        final_price = self.remaining_amt + self.extra_charge
        vals = {}
        account_invoice_obj = self.env['account.invoice']
        account_invoice_line_obj = self.env['account.invoice.line']
        booking = self.env['fleet.vehicle.booking'].browse(self._context['active_id'])
        partner_onchange = account_invoice_obj.onchange_partner_id('out_invoice', booking.customer_id.id)
        product_id = self.env['ir.model.data'].get_object_reference('spantree_logistics',
                                                                       'booking_charges_product')[1]
        product = self.env['product.product'].browse(product_id)
        product_line = account_invoice_line_obj.product_id_change(product_id,
                                                                  product.uom_id.id,
                                                                  qty=0, name='',
                                                                  type='out_invoice',
                                                                  partner_id=booking.customer_id.id)
        account_line_vals = {
            'account_analytic_id': False,
            'account_id': product_line['value'] and product_line['value']['account_id'] or False,
            'discount': 0,
            'invoice_line_tax_id': [[6, False, []]],
            'name': product_line['value'] and product_line['value']['name'] or False,
            'price_unit': final_price or 0.0,
            'product_id': product_id or False,
            'quantity': 1,
            'uos_id': product.uom_id and product.uom_id.id or False
        }
        vals.update({
            'partner_id': booking.customer_id and booking.customer_id.id or False,
            'fiscal_position': partner_onchange['value']['fiscal_position'] and partner_onchange['value']['fiscal_position'] or False,
            'journal_id': account_invoice_obj._default_journal() and (account_invoice_obj._default_journal()).id or False,
            'account_id': partner_onchange['value']['account_id'] and partner_onchange['value']['account_id'] or False,
            'currency_id': account_invoice_obj._default_currency() and (account_invoice_obj._default_currency()).id or False,
            'company_id': self.env['res.company']._company_default_get('account.invoice'),
            'invoice_line': account_line_vals and [(0, 0, account_line_vals)] or False,
            'vehicle_book_id': booking.id,
        })
        invoice_id = account_invoice_obj.create(vals)
#         return booking.write({'invoice_count': booking.invoice_count + 1})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: