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

from openerp.osv import osv, fields
from openerp.osv.orm import setup_modifiers
from lxml import etree

class op_all_student(osv.osv_memory):
    _inherit = 'op.all.student'

    _columns = {
        'student_tag_id':fields.many2one('registered.subject', string="Subject Tag")
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(op_all_student,self).default_get(cr, uid, fields, context=context)
        active_id = context.get('active_id')
        attendance_sheet_id = self.pool.get('op.attendance.sheet').browse(cr, uid, active_id)
        res['student_tag_id'] = attendance_sheet_id.subject_tag_id.id
        return res



    def onchange_student_tag_id(self, cr, uid, ids, student_tag_id, course_id, session_id, batch_id, context=None):
        """ Onchange funtion to pass dynamic domain for student ids to get student list by selected subject tags"""
        subj_line_obj = self.pool.get("subject.line")
        student_pool = self.pool.get("op.student")
        course_reg_pool = self.pool.get("course.registration")

        app_course_reg_list = []
        student_id_list= []
        res = {}

        if student_tag_id:
            subject_line_ids = subj_line_obj.search(cr, uid, [('subject_tags','=',student_tag_id)])
            for subject_line_id in subj_line_obj.browse(cr, uid, subject_line_ids):
                appr_course_ids = course_reg_pool.search(cr, uid, [('course_id','=',subject_line_id.course_id.id),('semester_id','=',subject_line_id.batch_id.id),('state','=','approved')])
                for course_id in course_reg_pool.browse(cr, uid, appr_course_ids):
                    app_course_reg_list.append(course_id)

            for app_course_id in app_course_reg_list:
                # student_id_list = student_pool.search(cr, uid, [('course_id','=',subject_line_id.course_id.id),
                #
                ## Fetch student from course registration only for approved courses                                         ('batch_id','=',subject_line_id.batch_id.id)])
                student_id_list.append(app_course_id.student_id.id)
            return {'value': res,'domain':{'student_ids':[('id','in',student_id_list)]}}
        else:
            return {'value': res,'domain':{'student_ids':[('course_id','=',course_id),('session_id','=',session_id),('batch_id','=',batch_id)]}}



    def check_subject(self, cr, uid, student, sheet_browse):
        ## Function to check where subject is elective or not
        course_reg_pool = self.pool.get("course.registration")
        course_reg_ids = course_reg_pool.search(cr, uid, [('student_id','=',student.id),('state','=','approved')])
        course_reg_ids = course_reg_pool.browse(cr, uid, course_reg_ids)
        for course_reg_id in course_reg_ids:
            elective_sub_list = [ele_sub.subject_id.id for ele_sub in course_reg_id.elective_subject_ids]
            if elective_sub_list:
                if sheet_browse.subject_id.subject_id.id in elective_sub_list:
                    return True
        return False

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """ Overrides orm field_view_get.
        @return: Dictionary of Fields, arch and toolbar.
        Overriding  """
        res = super(op_all_student, self).fields_view_get(cr, user, view_id, view_type, context)
        sheet_pool = self.pool.get('op.attendance.sheet')
        course_reg_pool = self.pool.get("course.registration")
        student_pool = self.pool.get("op.student")
        subj_line_obj = self.pool.get("subject.line")
        student_list = []
        app_course_reg_list = []
        student_id_list = []
        for sheet in context.get('active_ids',[]):
            sheet_browse = sheet_pool.browse(cr, user, sheet)
            course = sheet_browse.register_id.course_id.id
            session = sheet_browse.register_id.session_id.id
            batch = sheet_browse.register_id.batch_id.id
            division = sheet_browse.register_id.division_id.id
            absent_list = [x.student_id.id for x in sheet_browse.attendance_line]
            ## Apply logic for subject tag student fetch
            if sheet_browse.subject_tag_id:
                ## Get subject lines for selected tag
                subject_line_ids = subj_line_obj.search(cr, user, [('subject_tags','=',sheet_browse.subject_tag_id.id)])

                for subject_line_id in subj_line_obj.browse(cr, user, subject_line_ids):

                    ## Get approved course list
                    appr_course_ids = course_reg_pool.search(cr, user, [('course_id','=',subject_line_id.course_id.id),('semester_id','=',subject_line_id.batch_id.id),('state','=','approved')])
                    for course_id in course_reg_pool.browse(cr, user, appr_course_ids):
                        app_course_reg_list.append(course_id)

                for app_course_id in app_course_reg_list:
                    # student_id_list = student_pool.search(cr, uid, [('course_id','=',app_course_id.course_id.id),
                    #
                    ## Fetch student from course registration only for approved courses                                              ('batch_id','=',app_course_id.semester_id.id)])
                    student_id_list.append(app_course_id.student_id.id)
                all_student_search = [student_id for student_id in student_id_list]
            else:
                all_student_search = student_pool.search(cr, user, [('course_id','=',course),
                                                  ('session_id','=',session),
                                                   ('batch_id','=',batch),
                                                 ])
            for student_data in all_student_search:
                dic = {}
                student = student_pool.browse(cr,user, student_data)
                if sheet_browse.subject_id.select_subject == 'elective':
                    course_reg_ids = course_reg_pool.search(cr, user, [('student_id','=',student.id),('state','=','approved')])
                    course_reg_ids = course_reg_pool.browse(cr, user, course_reg_ids)
                    for course_reg_id in course_reg_ids:
                        elective_sub_list = [ele_sub.subject_id.id for ele_sub in course_reg_id.elective_subject_ids]
                        if elective_sub_list:
                            if sheet_browse.subject_id.subject_id.id in elective_sub_list:
                                student_list.append(student.id)
                                if view_type == "form":
                                   for field in res['fields']:
                                        doc = etree.XML(res['arch'])
                                        for node in doc.xpath("//field[@name='student_ids']"):
                                            domain = '[("id", "in", '+ str(student_list)+')]'
                                            node.set('domain', domain)
                                            res['arch'] = etree.tostring(doc)
                                            return res
                        else:
                            if view_type == "form":
                                for field in res['fields']:
                                    doc = etree.XML(res['arch'])
                                    for node in doc.xpath("//field[@name='student_ids']"):
                                        node.set('domain', "[('id', '=', [])]")
                                        # setup_modifiers(node, res['fields']['student_ids'])
                                        res['arch'] = etree.tostring(doc)
        return res

    def confirm_student(self, cr, uid, ids, context={}):
        value = {}
        result = False
        student_pool = self.pool.get("op.student")
        sheet_pool = self.pool.get('op.attendance.sheet')
        course_reg_pool = self.pool.get("course.registration")
        subj_line_obj = self.pool.get("subject.line")
        app_course_reg_list = []
        student_id_list = []
        data = self.read(cr, uid, ids)[0]

        student_ids = data['student_ids']

        data.update({'ids':context.get('active_ids',[]), 'student_ids': data['student_ids']})

        for sheet in context.get('active_ids',[]):
            sheet_browse = sheet_pool.browse(cr, uid, sheet)
            course = sheet_browse.register_id.course_id.id
            session = sheet_browse.register_id.session_id.id
            batch = sheet_browse.register_id.batch_id.id
            division = sheet_browse.register_id.division_id.id
            absent_list = [x.student_id.id for x in sheet_browse.attendance_line]


            ## Apply logic for subject tag student fetch
            if sheet_browse.subject_tag_id:
                ## Get subject lines for selected tag
                subject_line_ids = subj_line_obj.search(cr, uid, [('subject_tags','=',sheet_browse.subject_tag_id.id)])

                for subject_line_id in subj_line_obj.browse(cr, uid, subject_line_ids):

                    ## Get approved course list
                    appr_course_ids = course_reg_pool.search(cr, uid, [('course_id','=',subject_line_id.course_id.id),('semester_id','=',subject_line_id.batch_id.id),('state','=','approved')])
                    for course_id in course_reg_pool.browse(cr, uid, appr_course_ids):
                        app_course_reg_list.append(course_id)

                for app_course_id in app_course_reg_list:
                    # student_ids = student_pool.search(cr, uid, [('course_id','=',app_course_id.course_id.id),
                    #
                    ## Fetch student from course registration only for approved courses                                              ('batch_id','=',app_course_id.semester_id.id)])
                    student_id_list.append(app_course_id.student_id.id)
                all_student_search = [student_id for student_id in student_id_list]
            else:

                all_student_search = student_pool.search(cr, uid, [('course_id','=',course),
                                                                   ('session_id','=',session),
                                                                    ('batch_id','=',batch),
                                                                  ])
            all_student_search = list(set(all_student_search)-set(absent_list))


            for student_data in all_student_search:
                dic = {}
                student = student_pool.browse(cr,uid, student_data)
                if sheet_browse.subject_id.select_subject == 'elective':
                    result = self.check_subject(cr, uid, student, sheet_browse)
                    if result:
                        if student.id in data['student_ids']:
                            dic = {
                                   'student_id':student.id,
                                   'absent':False,
                                   'attendance_id': context.get('active_id'),
                                   }
                        else:
                            dic = {
                                   'student_id':student.id,
                                   'present':True,
                                   'attendance_id': context.get('active_id'),
                                   }
                        cr_id = self.pool.get('op.attendance.line').create(cr, uid, dic, context=context)
                else:
                    if student.id in data['student_ids']:
                        dic = {
                               'student_id':student.id,
                               'absent':False,
                               'attendance_id': context.get('active_id'),
                               }
                    else:
                        dic = {
                               'student_id':student.id,
                               'present':True,
                               'attendance_id': context.get('active_id'),
                               }
                    cr_id = self.pool.get('op.attendance.line').create(cr, uid, dic, context=context)
            value = {'type': 'ir.actions.act_window_close'}
            return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
