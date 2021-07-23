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
from datetime import datetime, timedelta, date
from openerp import SUPERUSER_ID


class fleet_parking_type(models.Model):
    _name = 'fleet.parking.type'

    code = fields.Char('Code')
    name = fields.Char('Name')
    hour_price = fields.Float(string="Hourly Price")
    charge_price = fields.Float(string='Daily Price')
    weekly_price = fields.Float(string="Weekly Price")
    fixed_price = fields.Float(string='Fixed Price')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    location_id = fields.Many2one('fleet.parking.location', 'Parking Location', required=True)
    _sql_constraints = [
        ('parking_code_uniq', 'unique(code)', 'Parking Code must be unique per Parking Type!'),
        ('name', 'unique(name)', 'Fleet Parking Type must be unique !')
    ]

    @api.one
    @api.constrains('hour_price', 'charge_price', 'weekly_price', 'fixed_price')
    def check_padding(self):
        if self.fixed_price < 0.0 or self.weekly_price < 0.0 or self.charge_price < 0.0 or self.hour_price < 0.0:
            raise Warning(_('Charges for vehicle can not be negative!'))

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(fleet_parking_type, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(fleet_parking_type, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(fleet_parking_type, self).unlink()


class fleet_parking_location(models.Model):
    _name = 'fleet.parking.location'

    @api.one
    @api.depends('code')
    def _default_name(self):
        self.name = self.code
        return self.code

    name = fields.Char('Name', required=True, compute=_default_name, readonly=False, store=True)
    city_id = fields.Many2one('fleet.city', 'City', required=True)
    capacity = fields.Integer('Capacity')
    location_id = fields.Many2one('stock.location', 'Location', readonly=True)
    code = fields.Char('Code', size=128, required=True)
    fare_ids = fields.One2many('fleet.parking.type', 'location_id', "parking Types")
    default_location = fields.Boolean(string='Set Location Default')

    _sql_constraints = [
        ('name', 'unique(name)', 'Fleet Parking Location must be unique !')
    ]

    @api.model
    def create(self, values):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        parent_location = self.env['ir.model.data'].get_object_reference('spantree_logistics', 'stock_location_parking')[1]
        location = self.env['stock.location'].sudo().create({'loc_barcode': False, 'scrap_location': False, 'valuation_in_account_id': False, 'name': values.get('name', ''), 'location_id': parent_location or False, 'company_id': 1, 'putaway_strategy_id': False, 'active': True, 'posz': 0, 'posx': 0, 'posy': 0, 'usage': 'internal', 'valuation_out_account_id': False, 'partner_id': False, 'comment': False, 'removal_strategy_id': False})
        values.update({'location_id': location.id})
        id = super(fleet_parking_location, self).create(values)
        return id

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if self._context.get('from_parking'):
            user_city = self.env['res.users'].browse(self._uid).parking_city_id
            if user_city:
                recs = self.search([('city_id', '=', user_city.id), ('capacity', '>', 0)] + args, limit=limit)
        else:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(fleet_parking_location, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(fleet_parking_location, self).unlink()


class fleet_parking(models.Model):
    _name = "fleet.parking"

    @api.multi
    def print_invoice(self):
        return self.env['report'].get_action(self.invoice_id, 'account.report_invoice')

    @api.model
    def create(self, vals):
        vals['number'] = self.env['ir.sequence'].get('parking')
        vals.update({'parking_user': self._uid})
        ret_val = super(fleet_parking, self).create(vals)
        if ret_val:
            if ret_val.start_time and ret_val.end_time and ret_val.start_time > ret_val.end_time:
                raise Warning('End date should be greater than start date.')
        return ret_val

    @api.multi
    def write(self, vals):
        ret_val = super(fleet_parking, self).write(vals)
        if ret_val:
            if self.start_time and self.end_time and self.start_time > self.end_time:
                raise Warning('End date should be greater than start date.')
        return ret_val

    @api.onchange('start_time', 'end_time')
    def onchange_dates(self):
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise Warning(_('End date should be greater than start date.'))

    @api.one
    @api.depends('start_time', 'end_time')
    def _compute_days_price(self):
        for each_self in self:
            if each_self.start_time and each_self.end_time:
                start_time = datetime.strptime(each_self.start_time, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(each_self.end_time, '%Y-%m-%d %H:%M:%S')
                total_days = (end_time - start_time).days + 1
                self.no_of_days = total_days


    @api.multi
    @api.depends('start_time', 'end_time', 'charge')
    def _compute_total_charge(self):
        for each_self in self:
            if each_self.start_time and each_self.end_time and each_self.charge:
                start_time = datetime.strptime(each_self.start_time, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(each_self.end_time, '%Y-%m-%d %H:%M:%S')
                total_days = (end_time - start_time).days + 1
                self.total_charge = each_self.charge * total_days

    type_id = fields.Many2one('fleet.parking.type', 'Parking Type', required=True)
    park_location_id = fields.Many2one('fleet.parking.location', 'Location', required=True, select=True)
    existing_cust = fields.Boolean('Select Existing Customer', default=True)
    customer_id = fields.Many2one('res.partner', 'Customer')
    cust_name = fields.Char('Customer Name',)
    charge = fields.Float('Charge', readonly=True)
    start_time = fields.Datetime('Start Time', required=True, default=fields.Datetime.now())
    end_time = fields.Datetime('End Time',)
    no_of_days = fields.Float(string="No. of Days", compute='_compute_days_price', default=0.0, store=True)
    total_charge = fields.Float(string="Total Charge", compute='_compute_total_charge', store=True)
    state = fields.Selection([('draft', 'Draft'), ('parked', 'Parked'), ('invoiced', 'Invoiced'), ('released', 'Released')], "State", default="draft")
    number = fields.Char('Parking No.', size=64, readonly=True)
    barcode = fields.Binary('Barcode', size=64,)
    invoice_id = fields.Many2one('account.invoice', "Invoice")
    license_plate = fields.Char('License Plate', size=128)
    to_be_invoiced = fields.Boolean('To be Invoiced')
    parking_user = fields.Many2one('res.users', "Parking User", readonly=True,)
    charge_type = fields.Selection([('fixed', 'Fixed'), ('hour', 'Hours'), ('daily', 'Daily'), ('week', 'Week')],
                                   string='Charges Based On')
    _rec_name = 'number'

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "%s" % (rec.number or rec.state)))
        return result

    @api.v7
    def make_payment(self, cr, uid, ids, context=None):
        #  not able to open wizard in return with new @api.one
        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'spantree_logistics', 'parking_payment_form')[1]
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'parking.payment',
                'view_id': [view_id],
                'type': 'ir.actions.act_window',
                'target':'new',
                }

    @api.one
    def create_cash_line(self):
        vals = {}
        account_invoice_obj = self.env['account.invoice']
        account_invoice_line_obj = self.env['account.invoice.line']
        journal_id = account_invoice_obj._default_journal()
        currency_id = account_invoice_obj._default_currency()
        partner_brw = self.customer_id or self.env['ir.model.data'].get_object_reference('transport_management', 'res_partner_parking')[1]
        partner_onchange = account_invoice_obj.onchange_partner_id(type='out_invoice', partner_id=partner_brw.id)
        product_brw = self.type_id.product_id
        product_onchange = account_invoice_line_obj.product_id_change(product_brw.id, product_brw.uom_id.id,
                                                                      qty=0, name='', type='out_invoice', partner_id=partner_brw.id)
        product_vals = {
            'account_analytic_id': False,
            'account_id': product_onchange['value'] and product_onchange['value']['account_id'] or False,
            'discount': 0,
            'invoice_line_tax_id': [[6, False, []]],
            'name': product_onchange['value'].get('name', ''),
            'price_unit': self.total_charge,
            'product_id': product_brw.id,
            'quantity': 1,
            'uos_id': product_brw.uom_id.id
        }
        vals.update({
            'partner_id': partner_brw.id,
            'name': self.customer_id.name or self.cust_name,
            'fiscal_position': partner_onchange['value']['fiscal_position'] and partner_onchange['value']['fiscal_position'] or False,
            'journal_id': journal_id and journal_id.id or False,
            'account_id': partner_onchange['value']['account_id'] and partner_onchange['value']['account_id'] or False,
            'currency_id': currency_id and currency_id.id or False,
            'company_id': self.env['res.company']._company_default_get('account.invoice'),
            'invoice_line': [(0, 0, product_vals)],
            'is_parking': True,
        })
        invoice_brw = account_invoice_obj.create(vals)
        invoice_brw.signal_workflow('invoice_open')
        self.make_invoice_paid(invoice_brw)
        self.write({'state': 'invoiced', 'invoice_id': invoice_brw.id})
        return {}

    @api.multi
    def make_invoice_paid(self, invoice_brw):
        '''this is the method which make the invoice paid'''
        if invoice_brw:
            vals_acc_voucher = {}
            user_record = self.env['res.users'].browse([self._uid])
            account_voucher_obj = self.env['account.voucher']
            journal_id = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', user_record.company_id.id)], limit=1)
            all_fields = account_voucher_obj.fields_get([])
            default_get_invoice_payment = account_voucher_obj.with_context({'journal_id':journal_id.id}).default_get(all_fields.keys())
            if invoice_brw.partner_id and invoice_brw.partner_id.parent_id:
                customer_id = invoice_brw.partner_id.parent_id
            else:
                customer_id = invoice_brw.partner_id
            res_onchange_journal_id = account_voucher_obj.onchange_journal(
                                                                    journal_id=journal_id.id,
                                                                    line_ids=[(6, 0, [])],
                                                                    tax_id=[],
                                                                    partner_id=customer_id.id,
                                                                    date=date.today(),
                                                                    amount=invoice_brw.amount_total,
                                                                    ttype='sale',
                                                                    company_id=customer_id.company_id.id,
                                                                )
            res_onchange_amount = account_voucher_obj.onchange_amount(
                                                        amount=invoice_brw.amount_total,
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

    @api.one
    def release_vehicle(self):
        self.state = 'released'


class parking_pass(models.Model):
    _name = "parking.pass"

    @api.multi
    def print_invoice(self):
        return self.env['report'].get_action(self.invoice_id, 'account.report_invoice')

    @api.one
    @api.constrains('validity')
    def check_no_of_days(self):
        if self.validity < 1:
            raise Warning(_('Pass can not be create for zero(0) day!'))

    @api.one
    @api.constrains('amount')
    def check_amount(self):
        if self.amount and self.amount < 0.0:
            raise Warning(_('Amount for parking pass can not be negative!'))

    @api.one
    @api.depends('start_date', 'end_date')
    def calculated_days(self):
        if self.start_date and self.end_date:
            waiting_time = ((datetime.strptime(self.end_date, '%Y-%m-%d')) - (datetime.strptime(self.start_date, '%Y-%m-%d'))).days
            self.validity = int(waiting_time)

    number = fields.Char('Pass Number', readonly=True)
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    vehicle_type_id = fields.Many2one('fleet.parking.type', 'Vehicle Type', required=True)
    parking_location_id = fields.Many2one('fleet.parking.location', 'Parking Location', required=True)
    validity = fields.Integer('Validity (In Days)', compute=calculated_days)
    start_date = fields.Date('Start Date', readonly=True)
    end_date = fields.Date('End Date', readonly=True)
    barcode = fields.Binary('Barcode', readonly=True)
    amount = fields.Float('Amount', required=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid') ], 'State', default='draft')

    _rec_name = 'number'

    @api.model
    def create(self, vals):
        vals['number'] = self.env['ir.sequence'].get('parking_pass')
        ret_val = super(parking_pass, self).create(vals)
        return ret_val

    @api.one
    def make_payment(self):
        vals = {}
        account_invoice_obj = self.env['account.invoice']
        account_invoice_line_obj = self.env['account.invoice.line']
        journal_id = account_invoice_obj._default_journal()
        currency_id = account_invoice_obj._default_currency()
        partner_brw = self.customer_id
        partner_onchange = account_invoice_obj.onchange_partner_id(type='out_invoice', partner_id=partner_brw.id)
        product_brw = self.vehicle_type_id.product_id
        product_onchange = account_invoice_line_obj.product_id_change(product_brw.id, product_brw.uom_id.id,
                                                                      qty=0, name='', type='out_invoice', partner_id=partner_brw.id)
        product_vals = {
            'account_analytic_id': False,
            'account_id': product_onchange['value'] and product_onchange['value']['account_id'] or False,
            'discount': 0,
            'invoice_line_tax_id': [[6, False, []]],
            'name': product_onchange['value'].get('name', ''),
            'price_unit': self.amount,
            'product_id': product_brw.id,
            'quantity': 1,
            'uos_id': product_brw.uom_id.id
        }
        vals.update({
            'partner_id': partner_brw.id,
            'name': self.customer_id.name or self.cust_name,
            'fiscal_position': partner_onchange['value']['fiscal_position'] and partner_onchange['value']['fiscal_position'] or False,
            'journal_id': journal_id and journal_id.id or False,
            'account_id': partner_onchange['value']['account_id'] and partner_onchange['value']['account_id'] or False,
            'currency_id': currency_id and currency_id.id or False,
            'company_id': self.env['res.company']._company_default_get('account.invoice'),
            'invoice_line': [(0, 0, product_vals)],
            'parking_pass_id': self. id,
            'pass_start_date': self.start_date,
            'pass_end_date': self.end_date,
        })
        invoice_brw = account_invoice_obj.create(vals)
        invoice_brw.signal_workflow('invoice_open')
        self.make_invoice_paid(invoice_brw)
        self.write({'state': 'paid', 'invoice_id': invoice_brw.id})
        return {}

    @api.multi
    def make_invoice_paid(self, invoice_brw):
        '''this is the method which make the invoice paid'''
        if invoice_brw:
            vals_acc_voucher = {}
            user_record = self.env['res.users'].browse([self._uid])
            account_voucher_obj = self.env['account.voucher']
            journal_id = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', user_record.company_id.id)], limit=1)
            all_fields = account_voucher_obj.fields_get([])
            default_get_invoice_payment = account_voucher_obj.with_context({'journal_id':journal_id.id}).default_get(all_fields.keys())
            if invoice_brw.partner_id and invoice_brw.partner_id.parent_id:
                customer_id = invoice_brw.partner_id.parent_id
            else:
                customer_id = invoice_brw.partner_id
            res_onchange_journal_id = account_voucher_obj.onchange_journal(
                                                                    journal_id=journal_id.id,
                                                                    line_ids=[(6, 0, [])],
                                                                    tax_id=[],
                                                                    partner_id=customer_id.id,
                                                                    date=date.today(),
                                                                    amount=invoice_brw.amount_total,
                                                                    ttype='sale',
                                                                    company_id=customer_id.company_id.id,
                                                                )
            res_onchange_amount = account_voucher_obj.onchange_amount(
                                                        amount=invoice_brw.amount_total,
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
    def view_invoice(self):
        view_id = self.env['ir.model.data'].get_object_reference('account', 'invoice_form')[1]
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': [view_id],
            'res_id': self.invoice_id.id if self.invoice_id else False,
            'type': 'ir.actions.act_window',
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
