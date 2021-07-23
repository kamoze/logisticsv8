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


    # def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    #        """ Overrides orm field_view_get.
    #        @return: Dictionary of Fields, arch and toolbar.
    #        Overriding  """
    #        res = super(op_all_student, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
    #        print res,'--------res'
    #        sheet_pool = self.pool.get('op.attendance.sheet')
    #        course_obj = self.pool.get('course.registration')
    #        subject_list = []
    #        student_list = []
    #        if 'active_id' in context:
    #            active_id = context.get('active_id')
    #            print active_id,'--------active_id'
    #            attendance_sheet_id = sheet_pool.browse(cr, user, active_id)
    #
    #         #    print attendance_sheet_id.register_id.course_id,'-------course_id'
    #            course_reg_ids = course_obj.search(cr, user, [('course_id','=',attendance_sheet_id.register_id.course_id.id), ('semester_id','=',attendance_sheet_id.register_id.batch_id.id), ('session_id','=',attendance_sheet_id.register_id.session_id.id),('state','=','approved')])
    #            for course_reg_id in course_obj.browse(cr, user, course_reg_ids):
    #             #    print course_reg_id.comp_subject_ids,'----------comp_subject_ids'
    #                subject_list = [comp_subject_id.subject_id.id for comp_subject_id in course_reg_id.elective_subject_ids]
    #                student_list.append(course_reg_id.student_id.id)
    #            if attendance_sheet_id.subject_id.subject_id.id in subject_list:
    #                if view_type == "form":
    #                    for field in res['fields']:
    #                         doc = etree.XML(res['arch'])
    #                         for node in doc.xpath("//field[@name='student_ids']"):
    #                             domain = '[("id", "in", '+ str(student_list)+')]'
    #                             node.set('domain', domain)
    #                             res['arch'] = etree.tostring(doc)
    #            else:
    #                if view_type == "form":
    #                    for field in res['fields']:
    #                         doc = etree.XML(res['arch'])
    #                         for node in doc.xpath("//field[@name='student_ids']"):
    #                             node.set('domain', "[('id', '=', [])]")
    #                             setup_modifiers(node, res['fields']['student_ids'])
    #                             res['arch'] = etree.tostring(doc)
    #        return res


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
        res = super(op_all_student, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        sheet_pool = self.pool.get('op.attendance.sheet')
        course_reg_pool = self.pool.get("course.registration")
        student_pool = self.pool.get("op.student")
        student_list = []
        for sheet in context.get('active_ids',[]):
            sheet_browse = sheet_pool.browse(cr, user, sheet)
            course = sheet_browse.register_id.course_id.id
            session = sheet_browse.register_id.session_id.id
            batch = sheet_browse.register_id.batch_id.id
            division = sheet_browse.register_id.division_id.id
            absent_list = [x.student_id.id for x in sheet_browse.attendance_line]
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
                        print elective_sub_list,'--------elective_sub_list'
                        if elective_sub_list:
                            if sheet_browse.subject_id.subject_id.id in elective_sub_list:
                                student_list.append(student.id)
                                print student_list,'--------student_list'
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
        #                            'stud_name' : student.name + ' ' + student.middle_name + ' ' +student.last_name,
                                   'absent':False,
                                   'attendance_id': context.get('active_id'),
                                   }
                        else:
                            dic = {
                                   'student_id':student.id,
        #                            'stud_name' : student.name + ' ' + student.middle_name + ' ' +student.last_name,
                                   'present':True,
                                   'attendance_id': context.get('active_id'),
                                   }
                        cr_id = self.pool.get('op.attendance.line').create(cr, uid, dic, context=context)
                else:
                    if student.id in data['student_ids']:
                        dic = {
                               'student_id':student.id,
    #                            'stud_name' : student.name + ' ' + student.middle_name + ' ' +student.last_name,
                               'absent':False,
                               'attendance_id': context.get('active_id'),
                               }
                    else:
                        dic = {
                               'student_id':student.id,
    #                            'stud_name' : student.name + ' ' + student.middle_name + ' ' +student.last_name,
                               'present':True,
                               'attendance_id': context.get('active_id'),
                               }
                    cr_id = self.pool.get('op.attendance.line').create(cr, uid, dic, context=context)
            value = {'type': 'ir.actions.act_window_close'}
            return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
