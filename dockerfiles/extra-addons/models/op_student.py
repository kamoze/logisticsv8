# -*- coding: utf-8 -*-
#/#############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2004-TODAY Tech-Receptives(<http://www.tech-receptives.com>).
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

from openerp.osv import fields, osv, orm
from openerp import models, api, _
from openerp import SUPERUSER_ID

class op_student(osv.osv):

    _inherit = 'op.student'
    _order = 'last_name'

    _columns ={
        'student_assessment_lines':fields.one2many('student.assessment.line.new','student_id', string="Student Assessment")
    }

    ## Inherit name get to change student name order by last name
    def name_get(self, cr, uid, ids, context=None):
        result= []
        if not all(ids):
            return result
        for student in self.browse(cr, uid, ids, context=context):
            # name = student.name+' '+student.middle_name+' '+student.last_name
            name = student.last_name+' '+student.middle_name+' '+student.name
            result.append((student.id,name))
        return result


class student_application(osv.osv):
    _inherit = 'student.application'


    def _get_details(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        # print skljdaslkdjf1
        for self_brw in self.browse(cr, uid, ids, context=context):
            res[self_brw.id] = {
                'utme1_details': '',
                'jamb_score': 0.0,
                'jamb_subject': '',
            }
            line_dict = {}
            # print skljdaslkdjf
            for line in self_brw.post_utme_line:
                line_dict[line.id] = line
            vals = line_dict.keys()
            jamb_score = 0
            jamb_subject = ''
            utme_details = ''
            if vals:
                vals.sort()
                jamb = line_dict.get(vals[-1], False)
                utme_details = str(jamb.name) + '/' + str(jamb.jamb_year_exam) + '/' + str(jamb.post_utme_center_id and jamb.post_utme_center_id.name)
                jamb_score = jamb.jamb_score
                for sub in jamb.jamb_subjects_ids:
                    jamb_subject += sub.name + '(' + str(sub.score) + ')' + ','
            res[self_brw.id]['utme1_details'] = utme_details
            res[self_brw.id]['jamb_score'] = jamb_score
            res[self_brw.id]['jamb_subject'] = jamb_subject
        return res

    def _get_lines(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('post.utme').browse(cr, uid, ids, context=context):
            result[line.student_application_id.id] = True
        return result.keys()

    _columns = {
        'utme1_details': fields.function(_get_details, string='UTME Details',type='char',multi='sums',
                                        store={
                                            'student.application': (lambda self, cr, uid, ids, c={}: ids, ['jamb_subjects_ids'], 10),
                                            'post.utme': (
                                            _get_lines, ['name', 'jamb_score', 'jamb_year_exam'], 10),
                                        },
                                          ),
        'jamb_score': fields.function(_get_details, string='JAMB Score', type='integer',multi='sums',
                                        store={
                                            'student.application': (lambda self, cr, uid, ids, c={}: ids, ['jamb_subjects_ids'], 10),
                                            'post.utme': (
                                            _get_lines, ['name', 'jamb_score', 'jamb_year_exam'], 10),
                                        },
                                        ),
        'jamb_subject': fields.function(_get_details, string='JAMB Score',type='char',multi='sums',
                                        store={
                                            'student.application': (lambda self, cr, uid, ids, c={}: ids, ['jamb_subjects_ids'], 10),
                                            'post.utme': (
                                            _get_lines, ['name', 'jamb_score', 'jamb_year_exam'], 10),
                                        },
                                      ),
    }


