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
from collections import OrderedDict
import StringIO
import time
import cStringIO
import base64
import csv
import xlwt
from xlwt import *
from xlwt import Workbook,easyxf
from numpy import *
import math
from openerp.osv import fields, osv, orm
from openerp.exceptions import except_orm
from openerp import _
from openerp.tools.translate import _
from pychart.afm import Courier_Oblique
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from datetime import datetime
from openerp import SUPERUSER_ID
import operator

class op_grade_calc_line(osv.osv):
    _inherit = 'op.grade.calc.line'

    _columns = {
            'use_new_student_assessment_line': fields.boolean(string="Use Student Assessment"),
            'student_assessment_lines' : fields.one2many('student.assessment.line.new','grade_line_id', 'Student Assessment'),
            'exam_score_lines' : fields.one2many('exam.score.lines','grade_line_id', 'Student Exam'),
    }


    def write(self, cr, uid, ids, vals, context=None):
        grade_calc_id = self.browse(cr, uid, ids)
        if vals.get("exam_score", False):
            # for part in self.browse(cr, uid, ids, context=context):
                # if part.payment_responsible_id <> vals["payment_responsible_id"]:
                #     #Find partner_id of user put as responsible
                #     responsible_partner_id = self.pool.get("res.users").browse(cr, uid, vals['payment_responsible_id'], context=context).partner_id.id
            # self.pool.get("op.gradepoint").message_post(cr, uid, 0,
            #                   body = _("You update values for "),
            #                   type = 'comment',
            #                   subtype = "mail.mt_comment", context = context,
            #                   model = 'op.gradepoint', res_id = grade_calc_id.gradepoint_gradecalc_id.id,
            #                   partner_ids = [uid])
            details = ""
            if vals:
                if 'exam_score' in vals:
                    details = "Exam Score updated to " + str(vals['exam_score'])
                if 'total_ca_score' in vals:
                    details += "<br/> Total CA upated to " + str(vals['total_ca_score'])
                if 'total_score' in vals:
                    details += " <br/> Total Score upated to " + str(vals['total_score'])
            subject = "Student Updated Values"
            self.pool.get("op.gradepoint").message_post(cr, uid, [grade_calc_id.gradepoint_gradecalc_id.id], body=details, subject=subject, context=context)
            # msg_id = self.pool.get("mail.thread").message_post(cr, uid, [grade_calc_id.gradepoint_gradecalc_id.id], body=_('Statement %s confirmed, journal items were created.') % vals['exam_score'], context=context)
            # # if msg_id:
            #     self.message_ids = [[0,0,{'subject':vals['exam_score']}]]
        return super(op_grade_calc_line, self).write(cr, uid, ids, vals, context=context)



class op_gradepoint(osv.osv):
    # _inherit =
    _name = 'op.gradepoint'
    _inherit = ['op.gradepoint', 'mail.thread', 'ir.needaction_mixin']






    ## Grade calculation for new lines form student assessment

    def student_assessment_lines_calculate_grade(self, cr, uid, ids, context=None):
        uid = SUPERUSER_ID
        sl_pool = self.pool.get('subject.line')
        assign_pool = self.pool.get('op.assignment')
        assign_sub_line_pool = self.pool.get('op.assignment.sub.line')

        op_exam_attendees_pool = self.pool.get('op.exam.attendees')

        op_attendance_line_pool = self.pool.get('op.attendance.line')

        op_grade_calc_line_pool = self.pool.get('op.grade.calc.line')


        for self_obj in self.browse(cr,uid,ids,context=context):
            if self_obj.grade_calculation_per_sem_line:
                inner_ids = op_grade_calc_line_pool.search(cr, uid, [('active','=',False),('gradepoint_gradecalc_id','=',self_obj.id)])
                if inner_ids:
                    op_grade_calc_line_pool.write(cr, uid, inner_ids, {'active':True}, context=context)
                self_obj = self.browse(cr,uid,self_obj.id)
                for gcpsl in self_obj.grade_calculation_per_sem_line:
                    sl_ids = sl_pool.search(cr,uid,[('subject_id','=',gcpsl.subject_id.id),('batch_id','=',self_obj.semester_id.id)])
                    sl_ids = sl_ids and sl_ids[0] or False
                    if sl_ids:
                        sl_obj = sl_pool.browse(cr,uid,sl_ids,context=context)
                        grade_dict = {'exam_score':0.0,'attendance_score':0.0,'total_ca_score':0.0,'total_score':0.0}
                        assignment_sub_lst = []
                        assignment_sub_ids_old_lst = []
                        op_exam_attendees_ids = []
                        op_attendance_line_ids = []
                        for aci in sl_obj.assessment_configuration_ids:
                            if aci.op_assessment_master_ids.ap_type=='ca':
                                domain = [
                                            ('student_id.id','=',self_obj.student_id.id),
                                            ('assignment_id.course_id.id','=',self_obj.course_id.id),
                                            ('assignment_id.subject_line_id.subject_id.id','=',gcpsl.subject_id.id),
                                            ('assignment_id.session_id.id','=',self_obj.session_id.id),
                                            ('assignment_id.batch_id.id','=',self_obj.semester_id.id),
                                            ('assignment_id.assignment_type.id','=',aci.op_assessment_master_ids.id),
    #                                             ('state','=','a'),
                                          ]
                                assign_total_per = 0
                                exam_mark = 0

                                assignment_sub_ids_old = assign_sub_line_pool.search(cr,uid,domain,context=context)
                                if assignment_sub_ids_old:
                                    assignment_sub_ids_old_lst.extend(assignment_sub_ids_old)
                                # print gcpsl.student_assessment_lines,'-----self.gcpsl.student_assessment_lines'
                                if gcpsl.student_assessment_lines:
                                    assignment_sub_lst = [rec.id for rec in gcpsl.student_assessment_lines]
                                    for asl_obj in self.pool.get('student.assessment.line.new').browse(cr,uid, assignment_sub_lst,context=context):
                                        # print asl_obj,'------------asl_obj'
                                        assign_total_per += asl_obj.obtained_marks
                                        grade_dict['total_ca_score']+=assign_total_per
                                        print assign_total_per, aci.percentage_weight, '---------assign_total_per---aci.percentage_weight'
                                    assign_score = assign_total_per * aci.percentage_weight / 100
                                    print assign_score,'------------assign_score 111111111111'
                                    # grade_dict['total_ca_score']+=assign_score
                                    ## get exam score
                                    if gcpsl.exam_score_lines:
                                        print gcpsl.exam_score_lines,'-------gcpsl.exam_score_lines'
                                        op_exam_rec = self.pool.get('exam.score.lines').browse(cr,uid,gcpsl.exam_score_lines.id,context=context)
                                        print op_exam_rec.marks,'---------------op_exam_rec'
                                        if op_exam_rec:
                                            exam_mark = op_exam_rec.marks
                                            print exam_mark,'-------exam_mark'
                                            grade_dict['exam_score'] = exam_mark
                                        else:
                                            grade_dict['exam_score'] = exam_mark

                                    grade_dict['total_ca_score'] = assign_total_per + exam_mark
                                # grade_dict.update({
                                #         'gradepoint_assignment_ids':[(6,0,assignment_sub_ids_old_lst)],
                                #        })

                            # if aci.op_assessment_master_ids.ap_type=='exam':
                            #         domain = [
                            #             ('studend_status','=','pass'),
                            #             ('student_id.id','=',self_obj.student_id.id),
                            #             ('exam_id.subject_id.id','=',gcpsl.subject_id.id),
                            #             ('exam_id.session_id.course_id.id','=',self_obj.course_id.id),
                            #             ('exam_id.session_id.session_id.id','=',self_obj.session_id.id),
                            #             ('exam_id.session_id.batch_id.id','=',self_obj.semester_id.id),
                            #             ]
                            #         exam_per = 0
                            #
                            #         op_exam_attendees_ids_old = op_exam_attendees_pool.search(cr,uid,domain,context=context)
                            #
                            #         op_exam_attendees_ids = [rec.id for rec in gcpsl.exam_score_lines]
                            #         if op_exam_attendees_ids:
                            #             for opaid in op_exam_attendees_ids:
                            #                 op_exam_rec = self.pool.get('exam.score.lines').browse(cr,uid,opaid,context=context)
                            #                 exam_per += op_exam_rec.marks
                            #                 grade_dict['exam_score']= exam_per * aci.percentage_weight / 100
                            #                 # grade_dict['exam_score']= exam_per
                            #         else:
                            #             grade_dict['exam_score']=0
                                    #
                            if aci.op_assessment_master_ids.ap_type=='attendance':
                                if sl_obj.attedence_selection == "Old":
                                     domain = [
                                               ('student_id.id','=',self_obj.student_id.id),
                                               ('attendance_id.subject_id.subject_id.id','=',gcpsl.subject_id.id),
                                               ('attendance_id.register_id.course_id.id','=',self_obj.course_id.id),
                                               ('attendance_id.register_id.session_id.id','=',self_obj.session_id.id),
                                               ('attendance_id.register_id.batch_id.id','=',self_obj.semester_id.id),
                                              ]
                                     count = 0.0
                                     op_attendance_line_ids = op_attendance_line_pool.search(cr, uid, domain, context=context)
                                     if op_attendance_line_ids:
                                         no_of_sheets = len(op_attendance_line_ids)
                                         for asid in op_attendance_line_ids:
                                             op_attendance_line_rec = op_attendance_line_pool.browse(cr,uid,asid,context=context)
                                             if op_attendance_line_rec.present == True:
                                                 count+=1
                                             attendance_score = count/no_of_sheets * 100
                                         grade_dict['attendance_score']+=attendance_score * aci.percentage_weight / 100
                                     else:
                                         grade_dict['attendance_score'] = 0
                                else:
                                     domain = [
                                               ('student_id.id','=',self_obj.student_id.id),
                                               ('attendance_id.subject_id.subject_id.id','=',gcpsl.subject_id.id),
                                               ('attendance_id.register_id.course_id.id','=',self_obj.course_id.id),
                                               ('attendance_id.register_id.session_id.id','=',self_obj.session_id.id),
                                               ('attendance_id.register_id.batch_id.id','=',self_obj.semester_id.id),
                                              ]
                                     count = 0.0
                                     present = 0.0
                                     absent = 0.0
                                     total = 0.0
                                     op_attendance_line_ids = op_attendance_line_pool.search(cr,uid,domain,context=context)
                                     op_att_line = op_attendance_line_pool.browse(cr, uid, op_attendance_line_ids, context)
                                     if op_att_line:
                                         for atten in op_att_line:
                                             if atten.present:
                                                 present += 1
                                             else:
                                                 absent += 1
                                         total = present + absent
                                         attendper = ((total - absent) / total) * 100
                                         if attendper >= sl_obj.base_attendence:
                                             attengread = (attendper - sl_obj.base_attendence) / (100 - sl_obj.base_attendence) * aci.percentage_weight
                                             grade_dict['attendance_score'] = attengread
                                         else:
                                             grade_dict['attendance_score'] = 0
                                     else:
                                             grade_dict['attendance_score'] = 0


                            grade_dict.update({
                                            #  'gradepoint_exam_ids':[(6,0,op_exam_attendees_ids_old)],
                                             'gradepoint_attendance_ids':[(6,0,op_attendance_line_ids)],
                                           })
                        o = op_grade_calc_line_pool.write(cr,uid,gcpsl.id,grade_dict,context=context)
                        cr.commit()
                    else:
                        raise except_orm(_('No Subject Line Found!'),
                        _("You have to define subject line for subject '%s' !") % (gcpsl.subject_id.name,))
        for self_obj in self.browse(cr, uid, ids):
            lists = []
            max_lists = []
            for sem in self_obj.semester_id.select_subject_line:
                for line in self_obj.grade_calculation_per_sem_line:
                    if sem.select_subject == 'elective' and line.subject_id.id == sem.subject_id.id:
                        lists.append({'id':line.id,'score':line.grade})
            if len(lists)>2:
                exclude_lists = sorted(lists, key=operator.itemgetter('score'))[2:]
                for ls in exclude_lists:
                    max_lists.append(ls['id'])
                op_grade_calc_line_pool.write(cr, uid, max_lists, {'active':False}, context=context)
                cr.commit()
        return True











    def update_calculate_grade(self, cr, uid, ids, context=None):
        uid = SUPERUSER_ID
        sl_pool = self.pool.get('subject.line')
        assign_pool = self.pool.get('op.assignment')
        assign_sub_line_pool = self.pool.get('op.assignment.sub.line')
        op_exam_attendees_pool = self.pool.get('op.exam.attendees')
        op_attendance_line_pool = self.pool.get('op.attendance.line')
        op_grade_calc_line_pool = self.pool.get('op.grade.calc.line')
        update_stud_obj = self.pool.get('updated.student.line')
        for self_obj in self.browse(cr,uid,ids,context=context):
            # print self_obj.grade_calculation_per_sem_line,'-----------self_obj.grade_calculation_per_sem_line'
            ca_lines = []
            exam_lines = []
            if self_obj.grade_calculation_per_sem_line:
                for gcpsl in self_obj.grade_calculation_per_sem_line:
                    updated_rec_id = update_stud_obj.search(cr, uid, [('grade_calc_line_id','=',gcpsl.id)])
                    # print updated_rec_id,'------------updated_rec_id'
                    for rec_id in update_stud_obj.browse(cr, uid, updated_rec_id):

                        for line_id in rec_id.ca_lines:
                            ## Logic to update CA lines and append to overwrite to main CA object
                            ca_vals = {
                                'obtain_marks': line_id.ca_obtain_mark,
                            }
                            ca_lines.append((1, line_id.op_assignment_sub_line_id.id, ca_vals))
                        # print rec_id.exam_lines,'----------------rec_id.exam_lines'
                        for line_id in rec_id.exam_lines:
                            ## Logic to update exam lines
                            exam_vals = {
                                'marks': line_id.exam_mark,
                            }
                            print exam_vals,'----------------exam_vals'
                            # print line_id.exam_attendees_id.id,'---to check------------exam_attendees_id,exam_attendees_id'
                            # exam_lines.append((1, line_id.exam_attendees_id.id, exam_vals))
                            line_id.exam_attendees_id.write(exam_vals)

                        print exam_lines,'-----------exam_lines'
                        ## Update student line record for related subject
                        new_update_vals = {
                                    'exam_score': rec_id.exam_score,
                                    'attendance_score': rec_id.attendance_score,
                                    # 'total_ca_score': rec_id.ca_score,
                                    'gradepoint_assignment_ids': ca_lines,
                                    'gradepoint_exam_ids': exam_lines,
                                    'total_score': rec_id.total_score,
                                    'grade': rec_id.grade,
                                    'grade_point': rec_id.grade_point,
                                }
                        op_grade_calc_line_pool.write(cr, uid, [rec_id.grade_calc_line_id.id], new_update_vals, context)

            ## Update on 30-AUG-2017
            ## To calculate grade on new lines entered in system
            if self_obj.grade_calculation_per_sem_line:
                for line in self_obj.grade_calculation_per_sem_line:
                    print line.use_new_student_assessment_line,'--------line.use_new_student_assessment_line'
                    if line.use_new_student_assessment_line:
                        self.student_assessment_lines_calculate_grade(cr, uid, ids, context=None)
                    # else:
                        self.pool.get('op.gradepoint').calculate_grade(cr, uid, ids, context=None)
        return True


class student_assessment_line_new(osv.osv):
    _name = 'student.assessment.line.new'

    _columns = {
        'student_id' : fields.many2one('op.student', 'Student'),
        'registered_subject': fields.many2one('registered.subject', 'Registered Subject'),
        'assignment_type': fields.many2one('op.assessment.master', 'Assignment Type'),
        'obtained_marks' : fields.float("Obtained Marks"),
        'percentage' : fields.float("Percentage %"),
        'grade_line_id' : fields.many2one('op.grade.calc.line', 'Grade Line')
    }

class exam_score_lines(osv.osv):
    _name = 'exam.score.lines'

    _columns = {
        'student_id' : fields.many2one('op.student', 'Student'),
        'status': fields.selection([('Present','Present'),('Absent','Absent')], string="Status"),
        'marks' : fields.float(" Marks"),
        'percentage' : fields.float("Percentage %"),
        'grade_line_id' : fields.many2one('op.grade.calc.line', 'Grade Line')
    }
