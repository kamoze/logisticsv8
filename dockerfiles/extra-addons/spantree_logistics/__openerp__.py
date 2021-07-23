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


{
    'name': 'Transport Management',
    'author': 'Spantree Ltd.',
    'website': 'http://www.spantreeng.com',
    'version': '1.0.1',
    'description': """
         Full Fledge Odoo Transport Module
    """,
    'depends': ['base', 'web', 'fleet', 'sale', 'account_accountant', 'hr_payroll', 'hr_expense', 'account_asset', 'stock'],
    "data": [
        'security/transport_security.xml',
        'security/ir.model.access.csv',
        'views/digital_sign_view.xml',
        'base/base_view.xml',
        'fleet/data.xml',
        'fleet/config_setting.xml',
        'fleet/wizard/parking_payment.xml',
        'fleet/wizard/booking_payment.xml',
        'fleet/wizard/trip_input_seat.xml',
        'fleet/wizard/vehicle_seats_compute_view.xml',
        'fleet/wizard/view_trip_board.xml',
        'fleet/wizard/wizard_scan_package_view.xml',
        'fleet/money_transfer_view.xml',
        'fleet/parking_view.xml',
        'fleet/booking_view.xml',
        'fleet/trip_view.xml',
        'fleet/package_management_view.xml',
        'fleet/luggage_fare_view.xml',
        'fleet/fleet_view.xml',
        'fleet/service_button_view.xml',
        'hr/hr_view.xml',
        'stock/stock.xml',
        'account/account_view.xml',
        'account/report_account_invoice_inherit.xml',
        'report.xml',
        'views/report_ticket_temp.xml',
        'views/report_return_ticket_temp.xml',
        'views/report_parking_template.xml',
        'views/report_source_dest_temp.xml',
        'views/report_dest_source_temp.xml',
        'views/report_seat_reservation_temp.xml',
        'views/vehicle_wise_booking_template.xml',
        'views/report_package_transfer_temp.xml',
        'views/report_package_waybill_template.xml',
        'views/report_money_transfer_temp.xml',
        'views/report_trip_boarding_chart_temp.xml',
        'views/report_trip_boarding_luggage_temp.xml',
        'views/report_parking_pass_template.xml',
        'wizard/order_analysis_wizard.xml',
        'wizard/print_tickets_wizard_view.xml',
        'views/report_order_analysis_template.xml',
        'wizard/wizard_waybill_view.xml',
        'wizard_seat_status/seat_status_wizard.xml',
        'email_template.xml',
        'sms_config_view.xml'
    ],
    'qweb': ['static/src/xml/digital_sign.xml'],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
