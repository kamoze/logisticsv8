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
from openerp.exceptions import except_orm
import time
from datetime import date
from openerp import SUPERUSER_ID
import random

class money_transfer_charge(models.Model):
    _name = 'money.transfer.charge'

    @api.one
    @api.constrains('amt_from', 'amt_to', 'amt_charged')
    def check_rate(self):
        if (self.amt_from and self.amt_from < 0.0) or (self.amt_to and self.amt_to < 0.0)\
            or (self.amt_charged and self.amt_charged < 0.0):
            raise Warning(_('Money transfer values can not zero(0).'))

    amt_from = fields.Float('Amount From', required=True)
    amt_to = fields.Float('Amount To', required=True)
    amt_charged = fields.Float('Transfer Fee', required=True)

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(money_transfer_charge, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(money_transfer_charge, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(money_transfer_charge, self).unlink()


class money_transfer(models.Model):
    _name = 'fleet.money.transfer'

    @api.one
    @api.depends('charge_percentage', 'charge_fixed', 'amount', 'based_on')
    def _compute_charges(self):
        charges_amount = 0.0
        currency_rate = 1.0
        if self.is_diff_currency is True:
            currency_rate = self.currency_rate
        if self.based_on == 'percentage':
            charges_amount = (self.amount * currency_rate * self.charge_percentage) / 100
            self.charges = charges_amount
        if self.based_on == 'fixed':
            self.charges = self.charge_fixed
        if self.based_on == 'calculated':
            if self.amount:
                mt_charge = self.env['money.transfer.charge'].search([('amt_from', '<=', self.amount),
                                                                      ('amt_to', '>=', self.amount)], limit=1)
                if not mt_charge:
                    raise except_orm(_('Error!'),
                                     _('Please define charge for this amount in Configuration -> Money Transfer Charge.'))
                self.charges = mt_charge.amt_charged

    @api.one
    @api.depends('amount', 'charges', 'charge_percentage', 'charge_fixed', 'based_on')
    def _compute_final_amount(self):
        currency_rate = 1.0
        if self.is_diff_currency is True:
            currency_rate = self.currency_rate
        self.final_amount = self.amount * currency_rate + self.charges

    @api.onchange('cust_id', 'receiver_id')
    def onchange_partner(self):
        if self.cust_id and self.cust_id.city_id:
            self.cust_city_id = self.cust_id.city_id.id
        if self.receiver_id and self.receiver_id.city_id:
            self.rec_city_id = self.receiver_id.city_id.id

    name = fields.Char(string='Transfer No.', copy=False, readonly=True, select=True)
    existing_cust = fields.Boolean(string='Select Existing Customer', default=True)
    cust_id = fields.Many2one('res.partner', string='Customer', required=True)
    cust_name = fields.Char(string="Customer Name")
    date = fields.Date(string='Date', copy=False, required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    payment_mode = fields.Selection([('cash', 'Cash'), ('bank', 'Bank'), ('debit', 'Debit'),
                                     ('credit', 'Credit')], string='Payment Mode', copy=False, required=True, default="cash")
    cheque_no = fields.Char(string='Cheque No', copy=False)
    amount = fields.Float(string='Amount To Transfer', copy=False)
    based_on = fields.Selection([('percentage', 'Percentage'), ('fixed', 'Fixed'), ('calculated', 'Calculated'), ],
                                string='Fee based on', copy=False, required=True, default='calculated')
    charge_percentage = fields.Float(string='Percentage (%)', copy=False)
    charge_fixed = fields.Float(string='Fixed Charges', copy=False)
    charges = fields.Float(string='Charges', compute='_compute_charges', readonly=True, copy=False)
    final_amount = fields.Float(string='Final Amount', compute='_compute_final_amount',
                                readonly=True, copy=False)
    refund_id = fields.Many2one('account.invoice', string='Refund Reference', readonly=True, copy=False)
    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference', readonly=True, copy=False)
    reason = fields.Text(string='Reason')
    receiver_id = fields.Many2one('res.partner', 'Receiver', required=True)
    state = fields.Selection([('draft', 'Draft'), ('receive', 'Received'),
                              ('paid', 'Paid'), ('cancel', 'Cancelled')], string='Status', readonly=True,
                             default='draft', copy=False)
    document_ids = fields.One2many('fleet.money.document', 'transfer_id', string='Transfer Document', copy=False)
    is_diff_currency = fields.Boolean('Is Different Currency')
    currency_id = fields.Many2one('res.currency', 'Currency')
    currency_rate = fields.Float('Currency Rate', help="currency rate will be multiplied to the current amount and then saved in final amount.")
    note = fields.Text('Note', copy=False)

    recieving_user = fields.Many2one('res.users', 'Receiving User', readonly=True, copy=False)
    paying_user = fields.Many2one('res.users', 'Paying User', readonly=True, copy=False)
    cust_city_id = fields.Many2one('fleet.city', "Customer City", required=True, readonly=False)
    rec_city_id = fields.Many2one('fleet.city', "Receiver City", required=True, readonly=False)
    signature = fields.Binary(string="Signature")
    _rec_name = 'cust_id'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('fleet.money.transfer') + str(random.randint(1000,99999))
        if vals.get('amount'):
            if vals['amount'] < 0:
                raise except_orm(_('Incorrect Input!'), ('You cannot enter negative values.'))
        if vals.get('charge_percentage'):
            if vals['charge_percentage'] < 0:
                raise except_orm(_('Incorrect Input!'), ('You cannot enter negative values.'))
        if vals.get('charge_fixed'):
            if vals['charge_fixed'] < 0:
                raise except_orm(_('Incorrect Input!'), ('You cannot enter negative values.'))
        vals.update({'recieving_user': self._uid})
        return super(money_transfer, self).create(vals)

    @api.one
    def write(self, vals):
        if vals.get('amount'):
            if vals['amount'] < 0:
                raise except_orm(_('Incorrect Input!'), ('You cannot enter negative values.'))
        if vals.get('charge_percentage'):
            if vals['charge_percentage'] < 0:
                raise except_orm(_('Incorrect Input!'), ('You cannot enter negative values.'))
        if vals.get('charge_fixed'):
            if vals['charge_fixed'] < 0:
                raise except_orm(_('Incorrect Input!'), ('You cannot enter negative values.'))
        return super(money_transfer, self).write(vals)

    @api.one
    def make_payment(self):
        vals = {}
        account_invoice_obj = self.env['account.invoice']
        account_invoice_line_obj = self.env['account.invoice.line']
        res_partner = account_invoice_obj.onchange_partner_id('out_invoice', self.cust_id.id)
        money_tran_id = self.env['ir.model.data'].get_object_reference('spantree_logistics',
                                                                       'product_product_money_transfer')[1]
        money_charges_id = self.env['ir.model.data'].get_object_reference('spantree_logistics',
                                                                          'product_product_money_transfer_service_charges')[1]
        money_tran_brw = self.env['product.product'].browse(money_tran_id)
        money_charges_brw = self.env['product.product'].browse(money_charges_id)
        product_money_transfer = account_invoice_line_obj.product_id_change(money_tran_id,
                                                                            money_tran_brw.uom_id.id,
                                                                            qty=0, name='',
                                                                            type='out_invoice',
                                                                            partner_id=self.cust_id.id)
        product_money_charges = account_invoice_line_obj.product_id_change(money_charges_id,
                                                                           money_charges_brw.uom_id.id,
                                                                            qty=0, name='',
                                                                            type='out_invoice',
                                                                            partner_id=self.cust_id.id)
        money_transfer_vals = {
            'account_analytic_id': False,
            'account_id': product_money_transfer['value'] and product_money_transfer['value']['account_id'] or False,
            'discount': 0,
            'invoice_line_tax_id': [[6, False, []]],
            'name': product_money_transfer['value'] and product_money_transfer['value']['name'] or False,
            'price_unit': self.amount and self.amount or False,
            'product_id': money_tran_id and money_tran_id or False,
            'quantity': 1,
            'uos_id': money_tran_brw.uom_id and money_tran_brw.uom_id.id or False
        }
        money_transfer_charges_vals = {
            'account_analytic_id': False,
            'account_id': product_money_charges['value'] and product_money_charges['value']['account_id'] or False,
            'discount': 0,
            'invoice_line_tax_id': [[6, False, []]],
            'name': product_money_charges['value'] and product_money_charges['value']['name'] or False,
            'price_unit': self.charges and self.charges or False,
            'product_id': money_charges_id and money_charges_id or False,
            'quantity': 1,
            'uos_id': money_charges_brw.uom_id and money_charges_brw.uom_id.id or False
        }
        vals.update({
            'partner_id': self.cust_id and self.cust_id.id or False,
            'fiscal_position': res_partner['value']['fiscal_position'] and res_partner['value']['fiscal_position'] or False,
            'journal_id': account_invoice_obj._default_journal() and (account_invoice_obj._default_journal()).id or False,
            'account_id': res_partner['value']['account_id'] and res_partner['value']['account_id'] or False,
            'currency_id': account_invoice_obj._default_currency() and (account_invoice_obj._default_currency()).id or False,
            'company_id': self.env['res.company']._company_default_get('account.invoice'),
            'invoice_line': money_transfer_vals and [(0, 0, money_transfer_vals), (0, 0, money_transfer_charges_vals)] or False,
            'money_transfer_id': self.id,
        })
        invoice_id = account_invoice_obj.create(vals)
        if invoice_id:
            self.write({'invoice_id': invoice_id.id})
            invoice_id.signal_workflow('invoice_open')
        self.write({'state': 'receive'})
        if self.cust_id.mobile:
            message = "Dear " + self.cust_id.name + ", We have received your value- Amt:" + str(self.amount) + ", Security Code:" + str(self.name) + ", Receiver:" + self.receiver_id.name + ", Payment Mode:" + self.payment_mode + ", Date:" + str(self.date)
            if message:
                self.env['sms.config'].send_sms(int(self.cust_id.mobile), message)
        return True

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
            if self.cust_id and self.cust_id.parent_id:
                customer_id = self.cust_id.parent_id
            else:
                customer_id = self.cust_id
            res_onchange_journal_id = account_voucher_obj.onchange_journal(
                                                                    journal_id=journal_id.id,
                                                                    line_ids=[(6, 0, [])],
                                                                    tax_id=[],
                                                                    partner_id=customer_id.id,
                                                                    date=date.today(),
                                                                    amount=self.final_amount,
                                                                    ttype='sale',
                                                                    company_id=customer_id.company_id.id,
                                                                )
            res_onchange_amount = account_voucher_obj.onchange_amount(
                                                        amount=self.final_amount,
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


    @api.multi
    def action_view_invoice(self):
        view_id = self.env['ir.model.data'].get_object_reference('account', 'invoice_form')[1]
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': [view_id],
            'res_id': self.invoice_id.id if self.invoice_id else False,
            'type': 'ir.actions.act_window',
        }

    @api.one
    def pay_amount(self):
        if self.invoice_id:
            self.make_invoice_paid(self.invoice_id.id)
        if self.cust_id.mobile:
            message = "Dear " + self.cust_id.name + ", Receiver:" + self.receiver_id.name + " paid for transaction:" + str(self.name) + " and Amt:" + str(self.amount) + ", Payment Mode:" + self.payment_mode
            if message:
                self.env['sms.config'].send_sms(int(self.cust_id.mobile), message)
        template_id = self.env.ref('spantree_logistics.spantree_logistics_email_money_trans_template', False)
        if template_id:
            template_obj = self.pool.get('email.template')
            template_obj.send_mail(self._cr , self._uid, template_id.id, self.id, True, context=None)
        self.write({'state': 'paid'})
        return {}

    @api.multi
    def action_transfer_cancel(self):
        self.write({'state': 'cancel'})
        return {}


class money_document(models.Model):
    _name = 'fleet.money.document'

    name = fields.Char(string='Name')
    document = fields.Binary(string='Document')
    transfer_id = fields.Many2one('fleet.money.transfer', 'Money Transfer')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: