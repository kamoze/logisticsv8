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
import datetime
import time
from datetime import date
from openerp.exceptions import except_orm, Warning, RedirectWarning


class report_order_analysis(models.AbstractModel):
    _name = 'report.spantree_logistics.report_order_analysis_template'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_order_analysis_template')
        wiz=self.env['order.analysis.wizard'].browse(data['ids'])
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs':wiz,
            'get_date': self._get_date,
            'get_end_date': self._get_end_date,
            'get_trips': self._get_trips,
            'get_parking': self._get_parking,
            'get_money_transfer': self._get_money_transfer,
            'get_package': self._get_package,
            'get_trip_context': self._get_trip_context,
            'get_parking_context': self._get_parking_context,
            'get_money_context': self._get_money_context,
            'get_package_context': self._get_package_context,
            'get_trips_total': self._get_trips_total,
            'get_package_total': self._get_package_total,
            'get_parking_total': self._get_parking_total,
            'get_money_transfer_total': self._get_money_transfer_total,
            'get_grand_total': self._get_grand_total,
        }
        return report_obj.render('spantree_logistics.report_order_analysis_template', docargs)

    def _get_date(self, form_data):
        access_list = []
        user_ids_in_access = []
        cashier_id = self.env['ir.model.data'].get_object_reference('spantree_logistics','group_cashier_user')[1]
        access_list.append(self.env['ir.model.data'].get_object_reference('base','group_erp_manager')[1])
        access_list.append(self.env['ir.model.data'].get_object_reference('base','group_system')[1])
        access_list.append(self.env['ir.model.data'].get_object_reference('spantree_logistics','group_transport_admin')[1])
        group_cashier = self.env['res.groups'].browse(cashier_id)
        user_ids_in_cashier = [x.id for x in group_cashier.users]
        for admin_group in self.env['res.groups'].browse(access_list):
            for user in admin_group.users:
                user_ids_in_access.append(user.id)
        if cashier_id and self._uid not in user_ids_in_access:
            new_start_date = date.today().strftime('%Y-%m-%d 0:0:0')
            return new_start_date
        elif cashier_id and self._uid in user_ids_in_access:
            if form_data.start_date:
                return form_data.start_date
            else:
                return False

    def _get_end_date(self, form_data):
        access_list = []
        user_ids_in_access = []
        cashier_id = self.env['ir.model.data'].get_object_reference('spantree_logistics','group_cashier_user')[1]
        access_list.append(self.env['ir.model.data'].get_object_reference('base','group_erp_manager')[1])
        access_list.append(self.env['ir.model.data'].get_object_reference('base','group_system')[1])
        access_list.append(self.env['ir.model.data'].get_object_reference('spantree_logistics','group_transport_admin')[1])
        group_cashier = self.env['res.groups'].browse(cashier_id)
        user_ids_in_cashier = [x.id for x in group_cashier.users]
        for admin_group in self.env['res.groups'].browse(access_list):
            for user in admin_group.users:
                user_ids_in_access.append(user.id)
        if cashier_id and self._uid not in user_ids_in_access:
            new_end_date = date.today().strftime('%Y-%m-%d 23:59:59')
            return new_end_date
        elif cashier_id and self._uid in user_ids_in_access:
            if form_data.end_date:
                return form_data.end_date
            else:
                return False

    def get_single_trip(self, args):
        single_args = args[:]
        single_args.append(('return_trip', '=', False))
        single_trip = self.env["fleet.trip.reservation"].search(single_args)
        return single_trip

    def get_round_trip(self, args):
        round_args = args[:]
        round_args.append(('return_trip', '=', True))
        round_trip = self.env["fleet.trip.reservation"].search(round_args)
        return round_trip

    def _get_trips(self,form_data):
        trip_res_obj = self.env["fleet.trip.reservation"]
        args = []
        total_amt = 0.0
        round_trip = False
        single_trip = False
        if self._get_date(form_data):
            args.append(("booking_date",">=",self._get_date(form_data)))
        if self._get_end_date(form_data):
            args.append(("booking_date","<=",self._get_end_date(form_data)))
        if form_data.user_id:
            args.append(("booking_user","=",form_data.user_id.id))
        args.append(('state', '=', 'confirmed'))
        single_trip = self.get_single_trip(args)
        round_trip = self.get_round_trip(args)
        trip_list =[]
        for single in single_trip:
            for seat_line in single.seat_ids:
                trip_dict = {}
                trip_dict.update({'origin' : seat_line.source_id.name,
                                  'destination' : seat_line.dest_id.name,
                                  'amount' : seat_line.price, 
                                  'ticket' : 1,
                                  'type' : 'Single Trip',
                                  'passenger_type' : seat_line.passenger_type.name,
                                })
                flag = False
                for trip_item in trip_list:
                    if (trip_item['origin'] == trip_dict['origin']) and (trip_item['destination'] == trip_dict['destination']) and\
                        (trip_item['type'] == trip_dict['type']) and (trip_item['passenger_type'] == trip_dict['passenger_type']):
                        trip_item['amount'] = trip_item['amount'] + trip_dict['amount']
                        trip_item['ticket'] = trip_item['ticket'] + trip_dict['ticket']
                        flag = True
                if not flag:
                    trip_list.append(trip_dict)
        for round in round_trip:
            for seat_line in round.seat_ids:
                if seat_line.source_id.id == round.source_id.id:
                    trip_dict = {}
                    trip_dict.update({
                                'origin' : seat_line.source_id.name,
                                'destination' : seat_line.dest_id.name,
                                'amount' : seat_line.price, 
                                'ticket' : 1,
                                'type' : 'Round Trip',
                                'passenger_type' : seat_line.passenger_type.name,
                            })
                    round_flag = False
                    for trip_item in trip_list:
                        if (trip_item['origin'] == trip_dict['origin']) and (trip_item['destination'] == trip_dict['destination']) and \
                            (trip_item['type'] == trip_dict['type']) and (trip_item['passenger_type'] == trip_dict['passenger_type']):
                            trip_item['amount'] = trip_item['amount'] + trip_dict['amount']
                            trip_item['ticket'] = trip_item['ticket'] + trip_dict['ticket']
                            round_flag = True
                    if not round_flag:
                        trip_list.append(trip_dict)
        return trip_list

    def _get_trips_total(self,form_data):
        total_amt = 0.0
        trips_list = self._get_trips(form_data)
        for trips in trips_list:
            if trips['amount']:
                total_amt += trips['amount']
        return total_amt

    def _get_parking(self,form_data):
        parking_res_obj = self.env["fleet.parking"]
        args = []
        park_list = []
        if self._get_date(form_data):
            args.append(("start_time",">=",self._get_date(form_data)))
        if self._get_end_date(form_data):
            args.append(("start_time","<=",self._get_end_date(form_data)))
#         args = [("start_time",">=",self._get_date(form_data)),("start_time","<=",self._get_end_date(form_data))]
        if form_data.user_id:
            args.append(("parking_user","=",form_data.user_id.id))
        parking_res_ids = parking_res_obj.search(args)
        for park in parking_res_ids:
            park_dict = {}
            park_dict.update({'location_name': park.park_location_id.name,
                              'price' : park.total_charge})
            flag = False
            for parking in park_list:
                if (parking['location_name'] == park_dict['location_name']):
                    parking['price'] = parking['price'] + park_dict['price']
                    flag = True
            if not flag:
                park_list.append(park_dict)
        return park_list

    def _get_parking_total(self,form_data):
        total_amt = 0.0
        park_list = self._get_parking(form_data) 
        for parking in park_list:
            total_amt += parking['price']
        return total_amt

    def _get_money_transfer(self,form_data):
        money_trans_obj = self.env["fleet.money.transfer"]
        args = []
        money_list = [] 
        if self._get_date(form_data):
            args.append(("date",">=",self._get_date(form_data)))
        if self._get_end_date(form_data):
            args.append(("date","<=",self._get_end_date(form_data)))
#         args = [("date",">=",self._get_date(form_data)),("date","<=",self._get_end_date(form_data))]
        if form_data.user_id:
            args.append(("recieving_user","=",form_data.user_id.id))
        money_trans_ids = money_trans_obj.search(args)
        for money in money_trans_ids:
            money_dict = {}
            money_dict.update({'origin' : money.cust_city_id.name,
                               'destination' : money.rec_city_id.name,
                               'amount_to_transfer' : money.amount,
                               'charges' : money.charges})
            flag = False
            for money_tran in money_list:
                if (money_tran['origin'] == money_dict['origin']) and\
                    (money_tran['destination'] == money_dict['destination']):
                    money_tran['amount_to_transfer'] = money_tran['amount_to_transfer'] + money_dict['amount_to_transfer']
                    money_tran['charges'] = money_tran['charges'] + money_dict['charges']
                    flag = True
            if not flag:
                money_list.append(money_dict)
        return money_list

    def _get_money_transfer_total(self,form_data):
        total_amt = 0.0
        money_list = self._get_money_transfer(form_data)
        for money_amt in money_list:
            total_amt += money_amt['amount_to_transfer'] + money_amt['charges']
        return total_amt

    def _get_package(self,form_data):
        package_trans_obj = self.env["fleet.package"]
        args = []
        package_list = []
        if self._get_date(form_data):
            args.append(("date",">=",self._get_date(form_data)))
        if self._get_end_date(form_data):
            args.append(("date","<=",self._get_end_date(form_data)))
#         args = [("date",">=",self._get_date(form_data)),("date","<=",self._get_end_date(form_data))]
        if form_data.user_id:
            args.append(("receive_user","=",form_data.user_id.id))
        package_trans_ids = package_trans_obj.search(args)
        for package in package_trans_ids:
            package_dict = {}
            package_dict.update({'origin' : package.source_loc_id.name,
                               'destination' : package.dest_loc_id.name,
                               'price' : package.price_on})
            flag = False
            for pack in package_list:
                if (pack['origin'] == package_dict['origin']) and\
                    (pack['destination'] == package_dict['destination']):
                    pack['price'] = pack['price'] + package_dict['price']
                    flag = True
            if not flag:
                package_list.append(package_dict)
        return package_list

    def _get_package_total(self,form_data):
        total_amt = 0.0
        package_list = self._get_package(form_data)
        for package_amt in package_list:
            total_amt += package_amt['price']
        return total_amt

    def _get_grand_total(self,form_data):
        grand_total = 0.0
        trip_amount = self._get_trips_total(form_data)
        parking_amount = self._get_parking_total(form_data)
        money_amount = self._get_money_transfer_total(form_data)
        package_amount = self._get_package_total(form_data)
        grand_total = trip_amount + parking_amount + money_amount + package_amount
        return grand_total

    def _get_trip_context(self):
        if self._context.get('print_trip'):
            return True
        else:
            return False

    def _get_parking_context(self):
        if self._context.get('print_parking'):
            return True
        else:
            return False

    def _get_money_context(self):
        if self._context.get('print_money'):
            return True
        else:
            return False

    def _get_package_context(self):
        if self._context.get('print_package'):
            return True
        else:
            return False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: