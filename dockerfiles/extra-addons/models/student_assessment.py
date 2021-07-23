# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api,fields, _
from openerp.exceptions import Warning as UserError

class StudentAssessment(models.Model):
    _name = 'student.assessment'
    _rec_name = "registred_sub_tags"


    registred_sub_tags = fields.Many2one('registered.subject', string="Registered Subject")
    # assessment_type = fields.Many2one('op.assessment.master', string="Assignment Type")
    student_assessment_lines = fields.One2many('student.assessment.lines', 'student_assessment_id', string="Student Assessment Lines")
    student_id = fields.Many2one('op.student', string="Student Id")
    subject_name = fields.Char(related="registred_sub_tags.subject_id.name", string="Subject Name")



    @api.model
    def create(self, vals):
        """ Inherit create method to pass default dc_mode as Non-Returnable when dc created from SO"""
        res = super(StudentAssessment, self).create(vals)
        return res

    @api.multi
    def create_line_ca1(self, stud_assessment_line):
        assignment_sub_lines = []
        ca1 = self.env['op.assessment.master'].search([('name','=', 'Continuous Assessment 1'),('ap_type','=','ca')],limit=1)
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': ca1.id,
            'obtained_marks':stud_assessment_line.ca1,
            'percentage':stud_assessment_line.ca1,
        }
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),
                                                    ('assignment_type','=',ca1.id), ('registered_subject','=', self.registred_sub_tags.id )])
        if student_assessment_lines:
            ## If lines already exits then delete them
            for student_assessment_line in student_assessment_lines:
                student_assessment_line.unlink()
        assignment_sub_lines.append([0,0, student_assessment_vals])
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                line.student_assessment_lines = assignment_sub_lines
        return True

    @api.multi
    def create_line_ca2(self, stud_assessment_line):
        assignment_sub_lines = []
        ca2 = self.env['op.assessment.master'].search([('name','=', 'Continuous Assessment 2'),('ap_type','=','ca')],limit=1)
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': ca2.id,
            'obtained_marks':stud_assessment_line.ca2,
            'percentage':stud_assessment_line.ca2,
        }
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),('assignment_type','=',ca2.id),
                                                                        ('registered_subject', '=',self.registred_sub_tags.id)])
        if student_assessment_lines:
            ## If lines already exits then delete them
            for student_assessment_line in student_assessment_lines:
                student_assessment_line.unlink()
        assignment_sub_lines.append([0,0, student_assessment_vals])
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                line.student_assessment_lines = assignment_sub_lines
        return True

    @api.multi
    def create_line_ca3(self, stud_assessment_line):
        assignment_sub_lines = []
        ca3 = self.env['op.assessment.master'].search([('name','=', 'Continuous Assessment 3'),('ap_type','=','ca')],limit=1)
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': ca3.id,
            'obtained_marks':stud_assessment_line.ca3,
            'percentage':stud_assessment_line.ca3,
        }
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),
                                                            ('assignment_type','=',ca3.id), ('registered_subject','=', self.registred_sub_tags.id )])
        if student_assessment_lines:
            ## If lines already exits then delete them
            for student_assessment_line in student_assessment_lines:
                student_assessment_line.unlink()
        assignment_sub_lines.append([0,0, student_assessment_vals])
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                line.student_assessment_lines = assignment_sub_lines
        return True

    @api.multi
    def create_line_ca4(self, stud_assessment_line):
        ca4 = self.env['op.assessment.master'].search([('name','=', 'Continuous Assessment 4'),('ap_type','=','ca')],limit=1)
        assignment_sub_lines = []
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': ca4.id,
            'obtained_marks':stud_assessment_line.ca4,
            'percentage':stud_assessment_line.ca4,
        }
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),
                                                                ('assignment_type','=',ca4.id), ('registered_subject','=', self.registred_sub_tags.id )])
        if student_assessment_lines:
            ## If lines already exits then delete them
            for student_assessment_line in student_assessment_lines:
                student_assessment_line.unlink()
        assignment_sub_lines.append([0,0, student_assessment_vals])
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                line.student_assessment_lines = assignment_sub_lines
        return True



    @api.multi
    def create_line_participation(self, stud_assessment_line):
        participation = self.env['op.assessment.master'].search([('name','=', 'Participation'),('ap_type','=','ca')],limit=1)
        assignment_sub_lines = []
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': participation.id,
            'obtained_marks':stud_assessment_line.participation,
            'percentage':stud_assessment_line.participation,
        }
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),
                                                        ('assignment_type','=',participation.id), ('registered_subject','=', self.registred_sub_tags.id )])
        if student_assessment_lines:
            ## If lines already exits then delete them
            for student_assessment_line in student_assessment_lines:
                student_assessment_line.unlink()
        assignment_sub_lines.append([0,0, student_assessment_vals])
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                line.student_assessment_lines = assignment_sub_lines
        return True

    @api.multi
    def create_line_exam_score(self, stud_assessment_line):
        exam_lines = []
        exam_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'status': 'Present',
            'marks':stud_assessment_line.exam_score,
            'percentage':stud_assessment_line.exam_score,
        }
        marks_ids = []
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                marks_ids.append(line.id)
        exam_lines_ids = self.env['exam.score.lines'].search([('student_id','=',stud_assessment_line.student_id.id),
                                                              ('grade_line_id','in', marks_ids)])
        if exam_lines_ids:
            ## If exam lines already exits then delete them
            for exam_lines_id in exam_lines_ids:
                exam_lines_id.unlink()

        exam_lines.append([0,0, exam_vals])
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                line.exam_score_lines = exam_lines
        return True

    @api.multi
    def update_student_attendance_marks(self, stud_assessment_line):
        """ Update student attendance scores """
        if stud_assessment_line and stud_assessment_line.grade_cal_line_id:
            stud_assessment_line.write({'attendance_score': stud_assessment_line.grade_cal_line_id.attendance_score})

    @api.multi
    def update_assessment(self):
        """ Funciton to create new lines for student
            assessment on garde calculation form
        """
        # assessment_obj = self.env['op.assessment']
        # assignment_obj = self.env['op.assignment']
        # assessment_master_obj = self.env['op.assessment.master']
        # sl_pool = self.env['subject.line']
        # mod_obj = self.pool.get('ir.model.data')
        model, res_id = self.env['ir.model.data'].get_object_reference('openeducat_erp', 'group_op_faculty')
        grp_ids = self.env['res.users'].search([('id','=',self._uid)]).read(['groups_id'])
        # grp_ids = grp_read.get('groups_id', [])
        security_flag = False
        if res_id in grp_ids:
            security_flag = True
        faculty_obj = self.env['op.faculty'].search([('emp_id.user_id','=',self._uid)])
        for stud_assessment_line in self.student_assessment_lines:
            if security_flag:
                department_ids = [dep.id for dep in faculty_obj.department_ids]
                if stud_assessment_line.student_id and stud_assessment_line.student_id.department_id \
                    and stud_assessment_line.student_id.department_id.id not in department_ids:
                    raise UserError(
                _('You are not allowed to Calculate Assessment for Student which are not from your department'))
            if stud_assessment_line.student_id.id == stud_assessment_line.grade_line_id.student_id.id:
                self.create_line_ca1(stud_assessment_line)
                self.create_line_ca2(stud_assessment_line)
                self.create_line_ca3(stud_assessment_line)
                self.create_line_ca4(stud_assessment_line)
                self.create_line_participation(stud_assessment_line)
                self.create_line_exam_score(stud_assessment_line)

                ##call function to update student attendace marks
                self.update_student_attendance_marks(stud_assessment_line)

        return True



    @api.onchange('registred_sub_tags')
    def onchange_subject_tags(self):
        sl_pool = self.env['subject.line']
        assessment_obj = self.env['op.assessment']
        assessment_master_obj = self.env['op.assessment.master']
        course_obj = self.env['course.registration']
        grade_calc_obj = self.env['op.assignment.sub.line']
        gradepoint_obj = self.env['op.gradepoint']
        stud_list = []
        app_course_list = []
        student_assessment_vals = {}
        if self.registred_sub_tags:
            subject_line_ids = sl_pool.search([('subject_tags','=',self.registred_sub_tags.id)])
            for subject_line_id in subject_line_ids:
                appr_course_ids = course_obj.search([('course_id','=',subject_line_id.course_id.id),

                                                     ('semester_id','=',subject_line_id.batch_id.id),
                                                     ('state','=','approved')])
                for course_id in appr_course_ids:
                    app_course_list.append(course_id)
           
            for appr_course_id in set(app_course_list):
                grade_point_ids = gradepoint_obj.search([('student_id','=',appr_course_id.student_id.id),('course_id','=',appr_course_id.course_id.id),('semester_id','=',appr_course_id.semester_id.id)])
                for grade_point_id in grade_point_ids:
                    for line in grade_point_id.grade_calculation_per_sem_line:
                        if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                            student_assessment_vals = {
                                'student_id': appr_course_id.student_id.id,
                                # 'exam_score': line.exam_score,
                                'attendance_score': line.attendance_score,
                                # 'total_score':line.total_score,
                                'grade_point':line.grade_point,
                                'grade_line_id':grade_point_id.id,
                                'grade_cal_line_id':line.id,
                                'grade':line.grade,
                                'course_reg_id': appr_course_id.id,
                            }
                            stud_list.append([0,0, student_assessment_vals])
            self.student_assessment_lines = stud_list

        res = {}

        return res

class StudentAssessmentLines(models.Model):
    _name = 'student.assessment.lines'

    @api.depends('ca1','ca2','ca3','ca4','participation','exam_score','attendance_score')
    def _get_total_score(self):
        for rec in self:
            rec.total_score = rec.ca1 + rec.ca2 + rec.ca3 + rec.ca4 + rec.participation + rec.exam_score + rec.attendance_score


    @api.depends('total_score')
    def _get_grade_point(self):
        for rec in self:
            if rec.student_assessment_id:
                subject_lines = self.env['subject.line'].search([('subject_tags','=',rec.student_assessment_id.registred_sub_tags.id)])
                for subject_line in subject_lines:
                    for grade_config in subject_line.gradepoint_configuration_ids:
                        if rec.total_score >= grade_config.grade_from and rec.total_score <= grade_config.grade_to:
                            rec.grade = grade_config.grade
                            rec.grade_point = grade_config.point


    student_id = fields.Many2one('op.student', string="Student")
    student_name = fields.Char(related="student_id.name", string="Student Name")
    student_middle_name = fields.Char(related="student_id.middle_name", string="Student Middle Name")
    student_last_name = fields.Char(related="student_id.last_name", string="Student Last Name")
    obtain_marks = fields.Char(string="Obtain Marks")
    ca1 = fields.Float(string="CA1")
    ca2 = fields.Float(string="CA2")
    ca3 = fields.Float(string="CA3")
    ca4 = fields.Float(string="CA4")
    participation = fields.Float(string="Participation")
    exam_score = fields.Float(string="Exam Score")
    attendance_score = fields.Float(string="Attendance Score")
    total_score = fields.Float(compute="_get_total_score", string="Total Score")
    grade = fields.Char(compute="_get_grade_point", string="Grade")
    grade_point = fields.Char(compute="_get_grade_point", string="Grade Point")
    grade_line_id = fields.Many2one('op.gradepoint')
    grade_cal_line_id = fields.Many2one('op.grade.calc.line', 'Grade Calc Line')
    student_assessment_id = fields.Many2one('student.assessment', string=" Assessment Id")
    course_reg_id = fields.Many2one('course.registration', string="Course Registered")
