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
import time
from datetime import datetime, date
from openerp import SUPERUSER_ID
import openerp.addons.product.product


class package_management(models.Model):
    _name = 'fleet.package'

    @api.one
    @api.depends('dest_loc_id', 'source_loc_id', 'package_cat_id', 'price_type', 'weight', 'volume', 'type_rate', 'delivery_charge')
    def _compute_charges(self):

        if self.package_cat_id and self.price_type:
            pack_fare = self.env['package.fare']
            if self.price_type == "fixed":
                if self.dest_loc_id and self.source_loc_id and self.package_cat_id:
                    fare_id = pack_fare.search([('package_cat_id', '=', self.package_cat_id.id), ('source_loc_id', '=', self.source_loc_id.id), ('dest_loc_id', '=', self.dest_loc_id.id)])
                    if not fare_id:
                        return True
#                         raise except_orm(_('No Fare Set!'), _('No fare found for this Package type between this Source and Destination'))
                    self.type_rate = fare_id.rate
                    self.price_on = fare_id.rate + self.delivery_charge
            if self.price_type == "weight":
                if self.weight and self.type_rate:
                    self.price_on = (self.weight * self.type_rate) + self.delivery_charge
            if self.price_type == "volume":
                if self.volume and self.type_rate:
                    self.price_on = (self.volume * self.type_rate) + self.delivery_charge
        return True

    @api.one
    @api.depends('sender_id', 'receiver_id')
    def _compute_city(self):
        if self.sender_id and self.sender_id.city_id:
            self.source_loc_id = self.sender_id.city_id
        if self.receiver_id and self.receiver_id.city_id:
            self.dest_loc_id = self.receiver_id.city_id

    @api.multi
    @api.depends('driver_id')
    def get_vehicle(self):
        if self.driver_id:
            fleet_id = self.env['fleet.vehicle'].search([('employee_driver_id', '=', self.driver_id.id)], limit=1)
            if fleet_id:
                self.fleet_id = fleet_id.id

    @api.multi
    @api.depends('state')
    def _get_package_number(self):
        for each in self:
            if each.id and not each.package_barcode:
                barcode = ''
                barcode = openerp.addons.product.product.sanitize_ean13("%s%s" % (datetime.now().strftime("%d%m%Y%f"), each.id))
                each.package_barcode = barcode

    name = fields.Char(string='Package Reference', copy=False, readonly=True, select=True)
    sender_id = fields.Many2one('res.partner', string='Sender')
    receiver_id = fields.Many2one('res.partner', string='Receiver')
    package_name = fields.Char(string="Package Name")
    package_desc = fields.Text(string='Package Description')
    date = fields.Datetime(string='Date', copy=False, required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    source_loc_id = fields.Many2one('fleet.city', string='Source Location', store=True, readonly=False, required=True)
    dest_loc_id = fields.Many2one('fleet.city', string='Destination Location', store=True, readonly=False, required=True)
    price_on = fields.Float(string='Price', copy=False, compute=_compute_charges, store=True)
    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference', readonly=True, copy=False)
    receiver_move = fields.Many2one('stock.move', string='Receiver Move', readonly=True, copy=False)
    transfer_move = fields.Many2one('stock.move', string='Transferred Move', readonly=True, copy=False)
    delivery_move = fields.Many2one('stock.move', string='Delivery Move', readonly=True, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('receive', 'Received'), ('transfer', 'Transferred'),
                              ('delivered', 'Delivered')], string='Status', readonly=True,)
    price_type = fields.Selection([('fixed', 'Fixed'), ('weight', 'Weight'), ('volume', 'Volume')], 'Charge ', required=True, default='fixed')
    volume = fields.Float('Volume')
    weight = fields.Float('Weight')
    type_rate = fields.Float('Rate',)
    receive_user = fields.Many2one('res.users', 'Receive User', readonly=True, copy=False)
    package_cat_id = fields.Many2one('package.category', 'Package Type', required=True)
    signature = fields.Binary(string="Signature")
    delivery_date = fields.Datetime(string="Delivery Date")
    driver_id = fields.Many2one('hr.employee', string="Employee")
    fleet_id = fields.Many2one('fleet.vehicle', string="Vehicle", compute=get_vehicle, store=True)
    package_barcode = fields.Char(string="Barcode", compute=_get_package_number, store=True, copy=False)
    delivery_charge = fields.Float(string="Delivery Charge")


    _defaults = {
        'name': lambda obj, cr, uid, context: '/',
        'state': 'draft',
    }

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(self._cr, self._uid, 'fleet.package') or '/'
        if vals.get('price_on'):
            if vals['price_on'] < 0:
                raise except_orm(_('Incorrect Input!'), ('You cannot enter negative values.'))
        vals.update({'receive_user': self._uid})
        return super(package_management, self).create(vals)

    @api.one
    def write(self, vals):
        if vals.get('price_on'):
            if vals['price_on'] < 0:
                raise except_orm(_('Incorrect Input!'), ('You cannot enter negative values.'))
        return super(package_management, self).write(vals)

    @api.one
    def create_move(self, product):
        move_val = {}
        move_obj = self.env['stock.move']
        move_default = move_obj.default_get(['invoice_state', 'priority', 'date_expected',
                                                           'partner_id', 'procure_method', 'picking_type_id',
                                                           'company_id', 'reserved_quant_ids', 'product_uom'])
        product_on_change = move_obj.onchange_product_id(product)
        source_loc_id = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_customers')[1]
        dest_loc_id = self.source_loc_id.location_id.id
        lot_id = self.env['stock.production.lot'].create({'name':self.name, 'product_id':product})
        move_val = {
            'product_id':product or False,
            'product_uom_qty': 1.0,
            'name': self.name,
            'location_id': source_loc_id or False,
            'location_dest_id': dest_loc_id or False,
            'restrict_lot_id': lot_id.id or False,
        }
        move_val.update(product_on_change.get('value'))
        move_brw = move_obj.create(move_val)
        move_brw.action_done()
        return self.write({'receiver_move':move_brw.id})

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
            if self.sender_id and self.sender_id.parent_id:
                customer_id = self.sender_id.parent_id
            else:
                customer_id = self.sender_id
            res_onchange_journal_id = account_voucher_obj.onchange_journal(
                                                                    journal_id=journal_id.id,
                                                                    line_ids=[(6, 0, [])],
                                                                    tax_id=[],
                                                                    partner_id=customer_id.id,
                                                                    date=date.today(),
                                                                    amount=self.price_on,
                                                                    ttype='sale',
                                                                    company_id=customer_id.company_id.id,
                                                                )
            res_onchange_amount = account_voucher_obj.onchange_amount(
                                                        amount=self.price_on,
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
    def confirm_package(self):
#         template_id = self.env.ref('spantree_logistics.email_pkg_accept_sender_template', False)
#         if template_id:
#             template_obj = self.pool.get('email.template')
#             template_obj.send_mail(self._cr , self._uid, template_id.id, self.id, True, context=None)
#         ctx = dict(self._context)
#         ctx.update({'package_accepted': True})
#         self.with_context(ctx).send_sms()
#         template_id = self.env.ref('spantree_logistics.email_pkg_accept_receiver_template', False)
#         if template_id:
#             template_obj = self.pool.get('email.template')
#             template_obj.send_mail(self._cr , self._uid, template_id.id, self.id, True, context=None)
#         self.with_context(ctx).send_sms()
        return self.write({'state': 'confirm'})

    @api.one
    def create_invoice(self):
        vals = {}
        account_invoice_obj = self.env['account.invoice']
        account_invoice_line_obj = self.env['account.invoice.line']
        res_partner = account_invoice_obj.onchange_partner_id('out_invoice', self.sender_id.id)
        product_package_id = self.env['ir.model.data'].get_object_reference('spantree_logistics',
                                                                       'product_product_package')[1]
        product_package_brw = self.env['product.product'].browse(product_package_id)
        product_package = account_invoice_line_obj.product_id_change(product_package_id,
                                                                            product_package_brw.uom_id.id,
                                                                            qty=0, name='',
                                                                            type='out_invoice',
                                                                            partner_id=self.sender_id.id)
        product_package_vals = {
            'account_analytic_id': False,
            'account_id': product_package['value'] and product_package['value']['account_id'] or False,
            'discount': 0,
            'invoice_line_tax_id': [[6, False, []]],
            'name': product_package['value'] and product_package['value']['name'] or False,
            'price_unit': self.price_on or False,
            'product_id': product_package_id or False,
            'quantity': 1,
            'uos_id': product_package_brw.uom_id and product_package_brw.uom_id.id or False
        }
        vals.update({
            'partner_id': self.sender_id and self.sender_id.id or False,
            'fiscal_position': res_partner['value'] and res_partner['value']['fiscal_position'] or False,
            'journal_id': account_invoice_obj._default_journal() and (account_invoice_obj._default_journal()).id or False,
            'account_id': res_partner['value'] and res_partner['value']['account_id'] or False,
            'currency_id': account_invoice_obj._default_currency() and (account_invoice_obj._default_currency()).id or False,
            'company_id': self.env['res.company']._company_default_get('account.invoice'),
            'invoice_line': product_package_vals and [(0, 0, product_package_vals)] or False,
            'package_id': self.id
        })
        invoice_id = account_invoice_obj.create(vals)
        self.write({'invoice_id': invoice_id.id})
        invoice_id.signal_workflow('invoice_open')
        template_id = self.env.ref('spantree_logistics.sender_email_pkg_in_prog_trans_template', False)
        if template_id:
            template_obj = self.pool.get('email.template')
            template_obj.send_mail(self._cr , self._uid, template_id.id, self.id, True, context=None)
        template_id = self.env.ref('spantree_logistics.receiver_email_pkg_in_prog_trans_template', False)
        if template_id:
            template_obj = self.pool.get('email.template')
            template_obj.send_mail(self._cr , self._uid, template_id.id, self.id, True, context=None)
        ctx = dict(self._context)
        ctx.update({'package_process': True})
        self.with_context(ctx).send_sms()
        self.make_invoice_paid(invoice_id.id)
        self.create_move(product_package_id)
        return True

        # account_bank_statement_line_obj = self.env['account.bank.statement.line']
#         cash_line_id ={}
#         account_bank_statement_obj_id = self.env['account.bank.statement'].search([('user_id','=',self._uid),('date','=',date.today().strftime('%Y-%m-%d')),('state', '=', 'open')])
#         if not account_bank_statement_obj_id:
#                 raise except_orm(_('Cash Register Not Found'), 
#                                  ('please contact to admin to create cash register'))
#         cash_line_id = account_bank_statement_line_obj.create({'date': self.date, 
#                                                                'name': 'Package' + '/' + self.name, 
#                                                                'amount': self.price_on,
#                                                                'statement_id': account_bank_statement_obj_id.id,
#                                                                'ref': self.package_desc,
#                                                                'partner_id': self.sender_id.id,
#                                                                })

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

    @api.one
    def action_receive_package(self):
        self.create_invoice()
        self.state = 'receive'
#         ctx = dict(self._context)
#         ctx.update({'package_received': True})
#         self.with_context(ctx).send_sms()
        return True

    @api.multi
    def action_print_invoice(self):
        if self and self.invoice_id:
            return self.env['report'].get_action(self.invoice_id, 'account.report_invoice')

    @api.one
    def create_delivery_move(self):
        move_obj = self.env['stock.move']
        move_default = move_obj.default_get(['invoice_state', 'priority', 'date_expected',
                                                           'partner_id', 'procure_method', 'picking_type_id',
                                                           'company_id', 'reserved_quant_ids', 'product_uom'])
        product = self.env['ir.model.data'].get_object_reference('spantree_logistics',
                                                                       'product_product_package')[1]
        product_on_change = move_obj.onchange_product_id(product)
        dest_loc_id = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_customers')[1]
        move_val = {
            'product_id':product or False,
            'product_uom_qty':1.0,
            'name': self.name,
            'location_id': self.dest_loc_id.location_id.id or False,
            'location_dest_id': dest_loc_id or False,
            'restrict_lot_id': self.receiver_move and self.receiver_move.restrict_lot_id.id or False,
        }
        move_val.update(product_on_change.get('value'))
        move_brw = move_obj.create(move_val)
        move_brw.action_done()
        template_id = self.env.ref('spantree_logistics.spantree_logistics_email_pkg_trans_done_template', False)
        if template_id:
            template_obj = self.pool.get('email.template')
            template_obj.send_mail(self._cr , self._uid, template_id.id, self.id, True, context=None)
        ctx = dict(self._context)
        ctx.update({'package_deliverd': True})
        self.with_context(ctx).send_sms()
        return self.write({'delivery_move':move_brw.id, 'state':'delivered'})

    @api.one
    def create_transfer_move(self):
        move_obj = self.env['stock.move']
#         move_default = move_obj.default_get(['invoice_state', 'priority', 'date_expected',
#                                                            'partner_id', 'procure_method', 'picking_type_id',
#                                                            'company_id', 'reserved_quant_ids', 'product_uom'])
        product = self.env['ir.model.data'].get_object_reference('spantree_logistics',
                                                                       'product_product_package')[1]
        product_on_change = move_obj.onchange_product_id(product)
        move_val = {
            'product_id': product or False,
            'product_uom_qty': 1.0,
            'name': self.name,
            'location_id': self.source_loc_id.location_id.id or False,
            'location_dest_id': self.dest_loc_id.location_id.id or False,
            'restrict_lot_id': self.receiver_move and self.receiver_move.restrict_lot_id.id or False,
        }
        move_val.update(product_on_change.get('value'))
        move_brw = move_obj.create(move_val)
        move_brw.action_done()
        template_id = self.env.ref('spantree_logistics.sender_email_pkg_trans_is_receive_template', False)
        if template_id:
            template_obj = self.pool.get('email.template')
            template_obj.send_mail(self._cr , self._uid, template_id.id, self.id, True, context=None)
        template_id = self.env.ref('spantree_logistics.receiver_email_pkg_trans_is_receive_template', False)
        if template_id:
            template_obj = self.pool.get('email.template')
            template_obj.send_mail(self._cr , self._uid, template_id.id, self.id, True, context=None)
        ctx = dict(self._context)
        ctx.update({'package_transfer': True})
        self.with_context(ctx).send_sms()
        return self.write({'transfer_move': move_brw.id, 'state':'transfer'})

    @api.multi
    def send_sms(self, package_id=None):
        if self._context.get('package_transfer'):
            if self.sender_id.mobile:
                message = "Dear " + self.sender_id.name + ", Your package with ID-" + self.name + " has been received at our destination terminal. Receiver can come for its package with a form of identification. Thanks."
                if message:
                    self.env['sms.config'].send_sms(int(self.sender_id.mobile), message)
            if self.receiver_id.mobile:
                message = "Dear " + self.receiver_id.name + ", Your package with ID-" + self.name + " has been received at our destination terminal. You can come for your package with a form of identification. Thanks."
                if message:
                    self.env['sms.config'].send_sms(int(self.receiver_id.mobile), message)
        elif self._context.get('package_process'):
            if self.sender_id.mobile:
                message = "Dear " + self.sender_id.name + ", Your package with ID-" + self.name + " is being processed. Thank you for your business."
                if message:
                    self.env['sms.config'].send_sms(int(self.sender_id.mobile), message)
            if self.receiver_id.mobile:
                message = "Dear " + self.receiver_id.name + ", You have a package with ID-" + self.name + " from-" + self.sender_id.name + " is being processed. Thank you for your business."
                if message:
                    self.env['sms.config'].send_sms(int(self.receiver_id.mobile), message)
        elif self._context.get('package_deliverd'):
            if self.sender_id.mobile:
                message = "Dear " + self.sender_id.name + ", Your package with ID-" + self.name + " is Deliverd to-" + self.receiver_id.name + ". We hope you had nice experience with us. Thanks for your continued patronage."
                if message:
                    self.env['sms.config'].send_sms(int(self.sender_id.mobile), message)
            if self.receiver_id.mobile:
                message = "Dear " + self.receiver_id.name + ", Your package with ID-" + self.name + " from-" + self.sender_id.name + " is Deliverd to you. We hope you had nice experience with us. Thanks for your continued patronage."
                if message:
                    self.env['sms.config'].send_sms(int(self.receiver_id.mobile), message)


class package_category(models.Model):
    _name = "package.category"

    name = fields.Char('Package Category', required=True)

    _sql_constraints = [
        ('name', 'unique(name)', 'Package Category must be unique !')
    ]

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(package_category, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(package_category, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(package_category, self).unlink()


class package_fare(models.Model):
    _name = "package.fare"

    @api.one
    @api.constrains('rate')
    def check_rate(self):
        if self.rate and self.rate < 0.0:
            raise Warning(_('Package transfer rate can not zero(0).'))

    package_cat_id = fields.Many2one('package.category', 'Category', required=True)
    rate = fields.Float('Rate', required=True)
    source_loc_id = fields.Many2one('fleet.city', string='Source Location', required=True)
    dest_loc_id = fields.Many2one('fleet.city', string='Destination Location', required=True)

    @api.model
    def create(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not create this record'),
                            ('please contact to admin to create a record'))
        return super(package_fare, self).create(vals)

    @api.one
    def write(self, vals):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not write this record'),
                            ('please contact to admin to write a record'))
        return super(package_fare, self).write(vals)

    @api.multi
    def unlink(self):
        if self._uid != SUPERUSER_ID and not self.env['res.users'].browse([self._uid]).has_group('spantree_logistics.group_transport_admin'):
            raise except_orm(_('You can not delete this record'),
                            ('please contact to admin to delete a record'))
        return super(package_fare, self).unlink()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: