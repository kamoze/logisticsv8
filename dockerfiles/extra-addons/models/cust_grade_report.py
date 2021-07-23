from openerp.osv import fields, osv
import datetime
from openerp import models, api, _
from openerp.exceptions import except_orm

class cust_grade_report(osv.osv):
    _name = 'cust.grade.report'

    _columns = {
              'course_id': fields.many2one('op.course', 'Course',required=True),
              'session_id': fields.many2one('op.sessions', 'Entry Session',required=True),
              'sem_ids': fields.many2one('op.batch', 'Semester'),
              'subject_id':fields.many2one('subject.line',"Subject"),
              'file_name':fields.binary('Report',readonly=True),
              'name' : fields.char('Name'),
              'cust_student_line_ids':fields.one2many('cust.student.line','cust_grade_report', 'Student'),

              }


    def onchange_course_id(self, cr, uid, ids, course, context=None):
        if course:
            model, res_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'openeducat_erp', 'group_op_faculty')
            grp_read = self.pool.get('res.users').read(cr, uid, uid, ['groups_id'])
            grp_ids = grp_read.get('groups_id',[])
            security_flag = False
            if res_id in grp_ids:
                course_brw = self.pool.get('op.course').browse(cr, uid, course)
                faculty_obj = self.pool.get('op.faculty').search(cr, uid, [('emp_id.user_id', '=', uid)])
                if faculty_obj:
                    fac_brw = self.pool.get('op.faculty').browse(cr, uid, faculty_obj[0])
                    department_ids = [dep.id for dep in fac_brw.department_ids]
                    if course_brw.department_id.id not in department_ids:
                        return {'warning': {'title': 'warning', 'message': 'You are not allowed to Update grade for course which is not in your department'},
                                'value': {'course_id': False}}


        return {'value': {}}



    def onchange_cust_subject_id(self, cr, uid, ids, subject, sem_id, context=None):
        '''
            ## THis function autopopulate all student's details when subject is selected

        '''
        ## Define Object Here
        grade_calc_obj = self.pool.get('op.grade.calc.line')
        subject_line_obj = self.pool.get('subject.line')
        cust_student_line_obj = self.pool.get('cust.student.line')
        ca_obj = self.pool.get('individual.ca.line')

        res = {}
        student_line = []
        ca_dict = []


        subject_line_id = subject_line_obj.search(cr, uid, [('id','=',subject)])

        if subject_line_id:
            line_id = subject_line_obj.browse(cr, uid, subject_line_id)
            grade_calc_ids = grade_calc_obj.search(cr, uid, [('subject_id','=', line_id.subject_id.id)])

            for grade_calc_id in grade_calc_obj.browse(cr, uid, grade_calc_ids):
                if  grade_calc_id.gradepoint_gradecalc_id.student_id.id and grade_calc_id.gradepoint_gradecalc_id.semester_id.id == sem_id:
                    cal_lines = []
                    exam_lines = []
                    for gradepoint_assignment_id in grade_calc_id.gradepoint_assignment_ids:
                        ca_vals = {
                            'ca_type': gradepoint_assignment_id.assignment_id.assignment_type.id,
                            'ca_obtain_mark': gradepoint_assignment_id.obtain_marks,
                            'op_assignment_sub_line_id': gradepoint_assignment_id.id,
                        }
                        ## Create Assignment wizard auto popup values
                        cal_lines.append((0,0,ca_vals))
                    for exam_id in grade_calc_id.gradepoint_exam_ids:
                        exam_vals = {
                            'exam_mark': exam_id.marks,
                            'exam_id': exam_id.exam_id.id,
                            'exam_attendees_id': exam_id.id,
                        }
                        ## Create Exam line auto wizard popup values
                        exam_lines.append((0,0,exam_vals))
                    cust_line_vals = {
                                        'student_id': grade_calc_id.gradepoint_gradecalc_id.student_id.id,
                                        'exam_score': grade_calc_id.exam_score,
                                        'attendance_score': grade_calc_id.attendance_score,
                                        'individual_ca_lines': cal_lines,
                                        'exam_lines': exam_lines,
                                        'ca_score': grade_calc_id.total_ca_score,
                                        'total_score': grade_calc_id.total_score,
                                        'grade': grade_calc_id.grade,
                                        'grade_point': grade_calc_id.grade_point,
                                        'grade_calc_line_id': grade_calc_id.id,
                                    }

                    cust_student_id = cust_student_line_obj.create(cr, uid, cust_line_vals)
                    student_line.append(cust_student_id)
        res = {
                'cust_student_line_ids': student_line,
            }
        return {'value': res}


    def cust_update_grade_point(self, cr, uid, ids, context):
        ## Call this function on wizard button
        return True



    ## IRINAL ONE KEEP FOR REFERANCE neefd to use this code nowwwwww
    def update_grade_point(self, cr, uid, student_rec, context):
        op_grade_calc_obj = self.pool.get('op.grade.calc.line')
        cal_lines = []
        exam_lines = []
        for line_id in student_rec.individual_ca_lines:
            ## Logic to update CA lines and append to overwrite to main CA object
            ca_vals = {
                'obtain_marks': line_id.ca_obtain_mark,
            }
            cal_lines.append((1, line_id.op_assignment_sub_line_id.id, ca_vals))
        ## Update exam Score
        for exam_line_id in student_rec.exam_lines:
            exam_vals = {
                'marks': exam_line_id.exam_mark,
            }
            # 'exam_attendees_id': line_id.exam_attendees_id.id,
            exam_lines.append((1, exam_line_id.exam_attendees_id.id, exam_vals))
        ## Update student line record for related subject
        new_update_vals = {
                    'exam_score': student_rec.exam_score,
                    'attendance_score': student_rec.attendance_score,
                    'total_ca_score': student_rec.ca_score,
                    'gradepoint_assignment_ids': cal_lines,
                    'gradepoint_exam_ids': exam_lines,
                    'total_score': student_rec.total_score,
                    'grade': student_rec.grade,
                    'grade_point': student_rec.grade_point,
                }
        rec = op_grade_calc_obj.write(cr, uid, [student_rec.grade_calc_line_id.id], new_update_vals, context)

        return rec



    ## This function will create new updated record in new relations
    def update_rec(self, cr, uid, student_rec, context):
        op_grade_calc_obj = self.pool.get('op.grade.calc.line')
        update_stud_obj = self.pool.get('updated.student.line')
        op_attendees_obj = self.pool.get('updated.op.exam.attendees.ext')
        exam_lies = []
        ca_lines = []
        exam_lines= []
        for line_id in student_rec.individual_ca_lines:
            ## Logic to update CA lines and append to overwrite to main CA object
            ca_vals = {
                'ca_type': line_id.ca_type.id,
                'ca_obtain_mark': line_id.ca_obtain_mark,
                'ca_line_id': line_id.id,
                'op_assignment_sub_line_id': line_id.op_assignment_sub_line_id.id,
            }
            ca_lines.append((0,0,ca_vals))

        ## Fetch Exam Lines to create new record in new object (updated.op.exam.attendees.ext')
        for line_id in student_rec.exam_lines:
            exam_vals = {
                'exam_mark': line_id.exam_mark,
                'exam_id': line_id.exam_id.id,
                'exam_attendees_id': line_id.exam_attendees_id.id,
            }
            exam_lines.append((0,0,exam_vals))

        cust_line_vals = {
                            'student_id': student_rec.student_id.id,
                            'exam_score': student_rec.exam_score,
                            'attendance_score': student_rec.attendance_score,
                            'ca_lines': ca_lines,
                            'exam_lines': exam_lines,
                            'ca_score': student_rec.ca_score,
                            'total_score': student_rec.total_score,
                            'grade': student_rec.grade,
                            'grade_point': student_rec.grade_point,
                            'grade_calc_line_id': student_rec.grade_calc_line_id.id,
                        }
        updated_line_id = update_stud_obj.search(cr, uid, [('grade_calc_line_id', '=', student_rec.grade_calc_line_id.id)])
        if not updated_line_id:
            update_stud_obj.create(cr, uid, cust_line_vals)
        else:
            line_id = update_stud_obj.browse(cr, uid, updated_line_id)
            new_vals = {
                            'student_id': student_rec.student_id.id,
                            'exam_score': student_rec.exam_score,
                            'attendance_score': student_rec.attendance_score,
                            'ca_lines': ca_lines,
                            'exam_lines': exam_lines,
                            'ca_score': student_rec.ca_score,
                            'total_score': student_rec.total_score,
                            'grade': student_rec.grade,
                            'grade_point': student_rec.grade_point,
                        }
            update_stud_obj.write(cr, uid, [line_id.id], new_vals, context)

        return True

    def create(self, cr, uid, vals, context):
        ## Define Object here
        op_grade_calc_obj = self.pool.get('op.grade.calc.line')
        stud_obj = self.pool.get('cust.student.line')
        student_lines = []
        if vals and 'cust_student_line_ids' in vals:
            for rec_id in vals.get('cust_student_line_ids'):
                student_lines.append(rec_id[1])
        res = super(cust_grade_report, self).create(cr, uid, vals)
        if student_lines:
            for student_rec in stud_obj.browse(cr, uid, student_lines):

                ## Call function to store updated exam lines
                self.update_rec(cr, uid, student_rec, context)
                self.update_grade_point(cr, uid, student_rec, context)

        return res


class cust_student_line(osv.osv_memory):
    _name = 'cust.student.line'

    @api.onchange('individual_ca_lines')
    def onchange_individual_ca_lines(self):
        res = {}
        sl_pool = self.env['subject.line']
        op_exam_attendees_ext_pool = self.env['op.exam.attendees.ext']
        exam_score = 0.0
        for ca_line in self.individual_ca_lines:
            sl_ids = sl_pool.search([('subject_id','=',ca_line.cust_student_line_id.grade_calc_line_id.subject_id.id),('batch_id','=',ca_line.cust_student_line_id.grade_calc_line_id.gradepoint_gradecalc_id.semester_id.id)])
            for aci in sl_ids.assessment_configuration_ids:
                if aci.op_assessment_master_ids.ap_type=='ca':
                    assign_total_per = 0
                    ## Get Updated exam lines
                    assign_total_per += ca_line.ca_obtain_mark
                    assign_score = assign_total_per * aci.percentage_weight / 100
                    ## Update CA score
                    self.ca_score = assign_score

    @api.onchange('exam_lines')
    def onchange_exam_lines(self):
        res = {}
        sl_pool = self.env['subject.line']
        op_exam_attendees_ext_pool = self.env['op.exam.attendees.ext']
        exam_score = 0.0
        for exam_line in self.exam_lines:
            sl_ids = sl_pool.search([('subject_id','=',exam_line.cust_student_line_id.grade_calc_line_id.subject_id.id),('batch_id','=',exam_line.cust_student_line_id.grade_calc_line_id.gradepoint_gradecalc_id.semester_id.id)])
            for aci in sl_ids.assessment_configuration_ids:
                if aci.op_assessment_master_ids.ap_type=='exam':
                    exam_per = 0
                    ## Get Updated exam lines
                    exam_per += exam_line.exam_mark
                    exam_score = exam_per * aci.percentage_weight / 100
                    ## Update exam score
                    self.exam_score = exam_score

    def write(self, cr, uid, ids, vals, context={}):
        res = super(cust_student_line, self).write(cr, uid, ids, vals, context=context)
        return res


    _columns = {
                'course_id':fields.many2one('op.course',"Course"),
                'student_id':fields.many2one('op.student', string='Student'),
                'exam_score':fields.float(string="Exam Score"),
                # 'exam_score': fields.function(_get_total_exam_scores, type="float", string="Exam Score"),
                'attendance_score':fields.float(string="Attendance Score"),
                'participation_score': fields.float(string="Participation"),
                'ca_score': fields.float(string="Total CA Score"),
                'total_score': fields.float(string="Total Score"),
                'grade': fields.char(string="Grade"),
                'grade_point': fields.integer(string="Grade Point"),
                'grade_calc_line_id': fields.many2one('op.grade.calc.line', string="Grade Calc Lines"),
                'cust_grade_report': fields.many2one('cust.grade.report', string="Grade Report"),
                'individual_ca_lines': fields.one2many('individual.ca.line', 'cust_student_line_id', 'CA List'),

                # ## Not using now keep for future
                'exam_lines':fields.one2many('op.exam.attendees.ext','cust_student_line_id', 'Exam Link'),
                # 'attenddance_line_ids':fields.many2many('op.attendance.line','gradecalc_line_attendance_rel',string='Attendance Lines'),
                # 'assignment_line_ids': fields.many2many('op.assignment.sub.line','gradecalc_line_assignment_rel',string='Assignment Lines'),

                }


class individual_ca_line(osv.osv_memory):
    _name = 'individual.ca.line'

    _columns = {
                    'ca_type': fields.many2one('op.assessment.master', string="Assignment Type"),
                    'ca_obtain_mark': fields.float(string="Obtain Mark"),
                    'op_assignment_sub_line_id': fields.many2one('op.assignment.sub.line', string='Sub Line Id'),
                    'cust_student_line_id': fields.many2one('cust.student.line', string="student Line Id")
                }



## Create new table for updated grade calc and ca lines
class updated_student_line(osv.osv_memory):
    _name = 'updated.student.line'

    def _get_total_ca_score(self, cr, uid, ids, field_name, arg, context={}):
        res= {}
        for id in self.browse(cr, uid, ids):
            total_ca_calculation = 0.0
            for ca_id in id.individual_ca_lines:
                total_ca_calculation += ca_id.ca_obtain_mark
            res[id.id] = total_ca_calculation
        return res

    _columns = {
                'course_id':fields.many2one('op.course',"Course"),
                'student_id':fields.many2one('op.student', string='Student'),
                'exam_score':fields.float(string="Exam Score"),
                'attendance_score':fields.float(string="Attendance Score"),
                'participation_score': fields.float(string="Participation"),
                'ca_score': fields.float(string="Total CA Score"), #fields.function(_get_total_ca_score, type="char", string="Total CA Score", size=15)
                'total_score': fields.float(string="Total Score"),
                'grade': fields.char(string="Grade"),
                'grade_point': fields.integer(string="Grade Point"),
                'grade_calc_line_id': fields.many2one('op.grade.calc.line', string="Grade Calc Lines"),
                'ca_lines': fields.one2many('updated.ca.line', 'student_line_id', 'CA List'),
                'exam_lines': fields.one2many('updated.op.exam.attendees.ext', 'student_line_id'),


                }



class updated_ca_line(osv.osv_memory):
    _name = 'updated.ca.line'

    _columns = {
                    'ca_type': fields.many2one('op.assessment.master', string="Assignment Type"),
                    'ca_obtain_mark': fields.float(string="Obtain Mark"),
                    'op_assignment_sub_line_id': fields.many2one('op.assignment.sub.line', string='Sub Line Id'),
                    'student_line_id': fields.many2one('updated.student.line', string="student Line Id")
                }




### Add New Object for Exam Lines
class op_exam_attendees_ext(osv.osv_memory):
    _name = 'op.exam.attendees.ext'

    def _get_total_exam_scores(self, cr, uid, ids, field_name, arg, context={}):
        ## Calculate total exam score
        res= {}
        for id in self.browse(cr, uid, ids):
            sl_pool = self.pool.get('subject.line')
            op_exam_attendees_ext_pool = self.pool.get('op.exam.attendees.ext')

            sl_ids = sl_pool.search(cr,uid,[('subject_id','=',id.grade_calc_line_id.subject_id.id),('batch_id','=',id.grade_calc_line_id.gradepoint_gradecalc_id.semester_id.id)])
            sl_ids = sl_ids and sl_ids[0] or False
            if sl_ids:
                sl_obj = sl_pool.browse(cr,uid,sl_ids,context=context)
                for aci in sl_obj.assessment_configuration_ids:
                    if aci.op_assessment_master_ids.ap_type=='exam':
                        ## Get Updated exam lines
                        op_exam_attendees_ids = id.exam_lines
                        exam_per = 0
                        ## Calculate exam score as per Configuration
                        if op_exam_attendees_ids:
                            for opaid in op_exam_attendees_ids:
                                exam_per += opaid.exam_attendees_id.per
                            res[id.id] = exam_per * aci.percentage_weight / 100
                        else:
                            res[id.id] = 0
        return res




    _columns = {
                    'exam_mark':fields.float(string="Exam Marks"),
                    'exam_id':fields.many2one('op.exam', string="Exam Marks"),
                    'exam_attendees_id': fields.many2one('op.exam.attendees', string="Exam Id"),
                    'cust_student_line_id': fields.many2one('cust.student.line', string="student Line Id"),
                }


### Add New Object for Exam Lines
### store updated exam lines here
class op_exam_attendees_ext(osv.osv_memory):
    _name = 'updated.op.exam.attendees.ext'

    _columns = {
                    'exam_mark':fields.float(string="Exam Marks"),
                    'exam_id':fields.many2one('op.exam', string="Exam Marks"),
                    'exam_attendees_id': fields.many2one('op.exam.attendees', string="Exam Id"),
                    'cust_student_line_id': fields.many2one('cust.student.line', string="student Line Id"),
                    'student_line_id': fields.many2one('updated.student.line')
                }

