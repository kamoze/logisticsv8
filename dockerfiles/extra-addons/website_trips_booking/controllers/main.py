# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
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

from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.web.http import request
from datetime import datetime, timedelta, date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import models, fields, api, _

class website_trips(http.Controller):

    @http.route(['/trips'], type='http', auth="public", website=True)
    def trip_main_menu(self, **post):
        value = self.checkout_trip_form_validate()
        value["passenger_type_list"]=""
        return request.website.render("website_trips_booking.index", value)


    @http.route(['/trips/locations'], type='json', auth="public", methods=['POST'], website=True)
    def list_of_trips_location(self):
        cr, uid, context = request.cr, request.uid, request.context
        trip_obj = request.registry['fleet.city']
        trip_ids = trip_obj.search(cr,SUPERUSER_ID,[])
        trip_name_list = []
        for trip_id in trip_ids:
            trip_name = trip_obj.read(cr,SUPERUSER_ID,trip_id,['name'])
            trip_name_list.append(trip_name['name'])
        return trip_name_list

    def checkout_trip_form_validate(self, data=None):
        # Validation
        validate_oneway_trip = ['departing_location','arriving_location','departing_on','number_of_passengers','ac_event_type','list_of_available_trips']
        validated_return_trip = ['departing_location','arriving_location','departing_on','arriving_on','number_of_passengers','ac_event_type','list_of_available_trips','list_of_return_trips']

        error = dict()
        form_val = dict()

        if not data:
            for field_name in validated_return_trip:
                form_val[field_name] = ''
                error[field_name] = ''
            form_val['ac_event_type'] = 'one_way'
        else:
            if data.get('ac_event_type')=='one_way':
                for field_name in validate_oneway_trip:
                    if data.get(field_name):
                        form_val[field_name] = ''

                for field_name in validate_oneway_trip:
                    if not data.get(field_name):
                        error[field_name] = 'missing'
                    else:
                        form_val[field_name] = data.get(field_name)
            else:
                for field_name in validated_return_trip:
                    if data.get(field_name):
                        form_val[field_name] = ''
                for field_name in validated_return_trip:
                    if not data.get(field_name):
                        error[field_name] = 'missing'
                    else:
                        form_val[field_name] = data.get(field_name)
        values = {
            'form_val':form_val,
            'error': error,
        }
        return values

    @http.route(['/trips/available'], type='http', auth="public", methods=['POST'], website=True)
    def validate_trip_form(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        return_trip =  False
        value = self.checkout_trip_form_validate(post)
        value['login_error_msg']=''
        value["passenger_type_list"]=""
        if uid == 3:
            return request.redirect("/web/login")
        if value['error'] or value['login_error_msg']:
            return request.website.render("website_trips_booking.index", value)

        city_obj = request.registry['fleet.city']
        passenger_type = request.registry['passenger.type']
        fleet_trip_obj = request.registry['fleet.trip']
        fleet_vehicle_obj = request.registry['fleet.vehicle']
        passenger_list = []
        temp = 0
        number_of_passengers = post['number_of_passengers']
        while temp < int(number_of_passengers):
            temp = temp + 1
            passenger_list.append(temp)

        passenger_type_ids = passenger_type.search(cr,SUPERUSER_ID,[])
        passenger_type_list = []
        source_id = city_obj.search(cr,SUPERUSER_ID,[('name','=',post['departing_location'])])
        dest_id = city_obj.search(cr,SUPERUSER_ID,[('name','=',post['arriving_location'])])
        if post['ac_event_type'] == 'one_way':
            return_trip = False
        else:
            return_trip = True
        default_price = fleet_vehicle_obj. _get_price_website(cr,SUPERUSER_ID,return_trip, int(post['list_of_available_trips']), passenger_type_ids[0], source_id[0], dest_id[0])
        for passenger_type_id in passenger_type_ids:
            price = fleet_vehicle_obj. _get_price_website(cr,SUPERUSER_ID,return_trip, int(post['list_of_available_trips']), passenger_type_id, source_id[0], dest_id[0])
            if price > 0.0:
                passenger_type_list.append((passenger_type_id, passenger_type.read(cr,SUPERUSER_ID,passenger_type_id,['name'])['name'],price))

        trips_information = fleet_trip_obj.read(cr,SUPERUSER_ID,int(post['list_of_available_trips']),['name','vehicle_id','start_time','end_time'])
        return_trip_information = {
            'name':'',
            'vehicle_id':'',
            'start_time':'',
            'end_time':'',
        }
        if post.has_key('list_of_return_trips'):
            return_trip_information = fleet_trip_obj.read(cr,SUPERUSER_ID,int(post['list_of_return_trips']),['name','vehicle_id','start_time','end_time'])
        return_trip_id = False
        if post.has_key('list_of_return_trips'):
            return_trip_id = post['list_of_return_trips']
        result = {
            'number_of_passengers':passenger_list,
            'source_id':source_id[0],
            'destination_id':dest_id[0],
            'default_price':default_price,
            'passenger_type_list':passenger_type_list,
            'trips_information':trips_information,
            'return_trip_information':return_trip_information,
            'departing_on':post['departing_on'],
            'trip_id':int(post['list_of_available_trips']),
            'departing_location':post['departing_location'],
            'arriving_location':post['arriving_location'],
            'total_passenger': post['number_of_passengers'],
            'arriving_on':post['arriving_on'],
            'return_trip_id':return_trip_id,
            'ac_event_type':post['ac_event_type'],
        }
        return request.website.render("website_trips_booking.available_trips", result)

    @http.route(['/trips/find-available-trips'], type='json', auth="public", methods=['POST'], website=True)
    def list_of_trips_avail(self, departing_from=None, arriving_at=None, departing_on=None, number_of_passengers=None,arriving_on=None,is_return_trip=None,**arg):
        cr, context = request.cr, request.context
        uid = SUPERUSER_ID
        trip_obj = request.registry['fleet.trip.reservation']
        city_obj = request.registry['fleet.city']
        fleet_trip_obj = request.registry['fleet.trip']
        source_id = city_obj.search(cr,uid,[('name','=',departing_from)])
        dest_id = city_obj.search(cr,uid,[('name','=',arriving_at)])

        avail_trips_name = []
        available_return_trip=[]
        if departing_on:
            departing_on_date = datetime.strptime(departing_on, "%d/%m/%Y")
            departin_date = date.strftime(departing_on_date, DEFAULT_SERVER_DATE_FORMAT)
            if source_id and dest_id and departin_date:
                avalil_trips = trip_obj.onchange_fill_trip(cr,uid,[],source_id[0],dest_id[0],departin_date,False)
                if avalil_trips:
                    for avalil_trip_id in avalil_trips['domain']['trip_id'][0][2]:
                        avail_trips_name.append((avalil_trip_id, fleet_trip_obj.read(cr,uid,avalil_trip_id,['name'])['name']))

        if is_return_trip:
            if arriving_on:
                arriving_on_date = datetime.strptime(arriving_on, "%d/%m/%Y")
                arriving_date = date.strftime(arriving_on_date, DEFAULT_SERVER_DATE_FORMAT)
                if source_id and dest_id and arriving_date:
                    avalil_trips_list = trip_obj.onchange_fill_return_trip(cr,uid,[],source_id[0],dest_id[0],arriving_date,departin_date,True)
                    if avalil_trips_list:
                        for avalil_trips_list_id in avalil_trips_list['domain']['return_trip_id'][0][2]:
                            available_return_trip.append((avalil_trips_list_id, fleet_trip_obj.read(cr,uid,avalil_trips_list_id,['name'])['name']))
        result={
            'avail_trips_name':avail_trips_name,
            'available_return_trip':available_return_trip
        }
        return result


    @http.route(['/trips/confirm'], type='http', auth="public", website=True)
    def ac_trip_confirm(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        trip_obj = request.registry['fleet.trip.reservation']
        res_users_obj = request.registry['res.users'].browse(cr,uid,uid)
        number_of_passengers = int(post['total_passenger'])
        if post['ac_event_type']=='one_way':
            i=1;
            trip_line_data = []
            while i<=number_of_passengers:
                # seat_no = seat_no+1
                trip_line_data.append((0,0, {'name':post['passenger_name'+str(i)],'passenger_type':post['passenger_type'+str(i)],'no_of_seat': 1}))
                i= i+1
            departing_on_date = datetime.strptime(post['trip_date'], "%d/%m/%Y")
            result = {
                'source_id': post['source_id'],
                'dest_id': post['destination_id'],
                'customer_id':res_users_obj.partner_id.id,
                'trip_date': date.strftime(departing_on_date, DEFAULT_SERVER_DATE_FORMAT),
                'trip_id':int(post['trip_id']),
                'seat_ids':trip_line_data,
            }
            context.update({'from_website':True})
            trip_created_id = trip_obj.create(cr,uid,result, context)
            return request.redirect('/web#id='+str(trip_created_id)+'&view_type=form&model=fleet.trip.reservation')
        elif post['ac_event_type']=='return_trip':
            i=1;
            trip_line_data = []
            while i<=number_of_passengers:
                trip_line_data.append((0,0, {'name':post['passenger_name'+str(i)],'passenger_type':post['passenger_type'+str(i)],'no_of_seat': 1}))
                i= i+1
            departing_on_date = datetime.strptime(post['trip_date'], "%d/%m/%Y")
            return_on_date = datetime.strptime(post['arriving_on'], "%d/%m/%Y")

            result = {
                'source_id': post['source_id'],
                'dest_id': post['destination_id'],
                'customer_id':res_users_obj.partner_id.id,
                'trip_date': date.strftime(departing_on_date, DEFAULT_SERVER_DATE_FORMAT),
                'trip_id':int(post['trip_id']),
                'seat_ids':trip_line_data,
                'return_trip':True,
                'return_date':date.strftime(return_on_date, DEFAULT_SERVER_DATE_FORMAT),
                'return_trip_id':int(post['return_trip_id']),

            }
            trip_created_id = trip_obj.create(cr,uid,result, context)
            return request.redirect('/web#id='+str(trip_created_id)+'&view_type=form&model=fleet.trip.reservation')

    @http.route(['/trips/get-price'], type='http', auth="public", methods=['POST'], website=True)
    def get_trip_price(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        return_trip =  False
        value = self.checkout_trip_form_validate(post)
        value["passenger_type_list"]=""
        if value['error']:
            return request.website.render("website_trips_booking.index", value)

        city_obj = request.registry['fleet.city']
        passenger_type = request.registry['passenger.type']
        fleet_trip_obj = request.registry['fleet.trip']
        fleet_vehicle_obj = request.registry['fleet.vehicle']
        passenger_type_ids = passenger_type.search(cr,SUPERUSER_ID,[])
        passenger_type_list = []
        source_id = city_obj.search(cr,SUPERUSER_ID,[('name','=',post['departing_location'])])
        dest_id = city_obj.search(cr,SUPERUSER_ID,[('name','=',post['arriving_location'])])
        if post['ac_event_type'] == 'one_way':
            return_trip = False
        else:
            return_trip = True
        default_price = fleet_vehicle_obj. _get_price_website(cr,SUPERUSER_ID,return_trip, int(post['list_of_available_trips']), passenger_type_ids[0], source_id[0], dest_id[0])
        for passenger_type_id in passenger_type_ids:
            price = fleet_vehicle_obj. _get_price_website(cr,SUPERUSER_ID,return_trip, int(post['list_of_available_trips']), passenger_type_id, source_id[0], dest_id[0])
            if price > 0.0:
                passenger_type_list.append((passenger_type_id, passenger_type.read(cr,SUPERUSER_ID,passenger_type_id,['name'])['name'],price))

        value["passenger_type_list"] = passenger_type_list
        return request.website.render("website_trips_booking.index", value)


class fleet_vehicle(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model
    def _get_price_website(self, return_trip, trip_id, passenger_type, source_id, dest_id):
        price = 0
        if trip_id and passenger_type and source_id and dest_id:
           trip_fare = self.env['trip.config.fare']
           trip_record = self.env['fleet.trip'].browse([trip_id])
           fleet_city = self.env['fleet.city']
           source_city = fleet_city.browse([source_id])
           dest_city = fleet_city.browse([dest_id])
           if not return_trip:
               fare = trip_fare.search([('route_id', '=', trip_record.route_id.id)])
               if fare:
                   for all_fares in fare.fare_lines:
                       if all_fares.from_city.id == source_city.id and all_fares.to_city.id == dest_city.id and not all_fares.round_trip:
                           for ptype in all_fares.passenger_types:
                               if ptype.id == passenger_type:
                                   price = all_fares.price
           else:
               fare = trip_fare.search([('route_id', '=', trip_record.route_id.id)])
               if fare:
                   for all_fares in fare.fare_lines:
                       if all_fares.from_city.id == source_city.id and all_fares.to_city.id == dest_city.id and all_fares.round_trip:
                            for ptype in all_fares.passenger_types:
                                if ptype.id == passenger_type:
                                    price = all_fares.price
        return price

