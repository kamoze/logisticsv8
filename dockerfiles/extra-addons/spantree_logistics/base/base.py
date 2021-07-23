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

from openerp import models, fields, api
from datetime import datetime, date, time
from openerp.exceptions import except_orm, Warning, RedirectWarning


class res_partner(models.Model):
    _inherit = "res.partner"

    city_id = fields.Many2one('fleet.city', "City")
    pin_no = fields.Char(string="Pin")
    kin_name = fields.Char(string="Next of Kin Name")
    kin_no = fields.Char(string="Next of Kin Number")

    _sql_constraints = [
       ('pin_no', 'unique(pin_no)', 'Pin must be unique !'),
    ]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            if self._context.get('transport'):
                recs = self.search(['|',('name', operator, name),('phone', operator, name)] + args, limit=limit)
            else:
                recs = self.search([('name', operator, name)] + args, limit=limit)
        else:
            recs = self.search(args, limit=limit)
        return recs.name_get()


class res_users(models.Model):
    _inherit = "res.users"


    parking_city_id = fields.Many2one('fleet.city', "Parking City")
    default_arrival_city_id = fields.Many2one('fleet.city', "Default Arrival City")
    pin_no = fields.Char(related='partner_id.pin_no', string="Pin")

    _sql_constraints = [
       ('pin_no', 'unique(pin_no)', 'Pin must be unique !'),
    ]

    @api.model
    def create_cash_register(self):
        """
        Creates cash register for each user
        """
        account_bank_statement_obj = self.env['account.bank.statement']
        context = dict(self._context)
        today_date = date.today().strftime('%Y-%m-%d')
        cashier_id = self.env['ir.model.data'].get_object_reference('spantree_logistics','group_cashier_user')[1]
        if cashier_id:
            for user in self.env['res.groups'].browse(cashier_id).users:
                cash_register = account_bank_statement_obj.search([('date','=',date.today().strftime('%Y-%m-%d')),('user_id','=', user.id)])
                if not cash_register:
                    context.update({'journal_type':'cash'})
                    default_value = account_bank_statement_obj.with_context(context).default_get(['period_id','user_id', 'journal_id','date'])
                    cash_register_id = account_bank_statement_obj.create({'user_id': user.id,
                                                                          'name': user.name + '_' + today_date,
                                                                          'balance_start': [],
                                                                          'journal_id': default_value['journal_id'],
                                                                          'details_ids': [],
                                                                          'move_line_ids': [],
                                                                          'period_id': default_value['period_id'],
                                                                          'closing_details_ids': [],
                                                                          'date': default_value['date'],
                                                                          'line_ids': []
                                                                         })
                    cash_register_id.button_open()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: