# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (c) 2011 OpenERP S.A. <http://openerp.com>
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
    'name': 'Spantree Sales Status',
    'version': '1.0',
    'category': 'Sales Management',
    'description': """
Provides functionality of SMS and Email
===============================================================
- send daily SMS and email for sales
- send sms and email when pos session close
- manually send email and sms also for sales
""",
    'author': 'Acespritech Solutions Pvt.Ltd',
    'website': 'http://www.acespritech.com',
    'depends': ['sale', 'point_of_sale','openeducat_erp','openeducat_ext'],
    'data' : [
        'security/ir.model.access.csv',
        'base/base_view.xml',
        'sale/wizard/so_pos_wizard_view.xml',
        'sale/wizard/wizard_mass_sms_email_view.xml',
        'sale/sale_data.xml',
    ],
    'auto_install': False,
    'installable': True,
}
