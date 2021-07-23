# -*- coding: utf-8 -*-
#/#############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2009-TODAY Tech-Receptives(<http://www.tech-receptives.com>).
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
#/#############################################################################

{
    'name': 'Student Grade Maagement',
    'version': '1',
    'category': 'Student Application',
    "sequence": 1,
    'summary': 'Manage Students Application Form',
    'complexity': "easy",
    'description': """
    """,
    'author': 'Tech-Receptives Solutions Pvt. Ltd.',
    'website': 'http://www.openeducat.org',
    'images': [],
    'depends': ['openeducat_ext'],
    'data': [
            'views/cust_grade_report_view.xml',
            'views/gradepoint_view.xml',
            'views/op_all_stident_wiard_view_attendance.xml',
            'views/ca_view.xml',
            'views/registred_subject_view.xml',
            'views/subject_line_view.xml',
            'views/student_assessment_view.xml',
        ],
    'test': [
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
