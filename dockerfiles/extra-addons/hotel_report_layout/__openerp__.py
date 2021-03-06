# -*- encoding: utf-8 -*-
#############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#############################################################################

{
    'name': 'Report Extended - ST5',
    'category': 'Base',
    'summary': 'Report',
    'version': '0.01',
    'description': """
        Report Extended Which Insert The Header Of Company's Full Address
        In Qweb Report
            """,
    "author": "SpantreeNG, Serpent Consulting Services Pvt. Ltd., OpenERP SA",
    "website": "http://www.spantreeng.com",
    'depends': ['report'],
    'data': [
        'views/layouts.xml',
    ],
    'installable': True,
    'auto_install': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
