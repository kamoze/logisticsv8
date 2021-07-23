# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api,fields, _

class StudentAssessment(models.TransientModel):
    _name = 'student.assessment'
    _rec_name = "registred_sub_tags"


    registred_sub_tags = fields.Many2one('registered.subject', string="Registered Subject")
    assessment_type = fields.Many2one('op.assessment.master', string="Assignment Type")
    student_assessment_lines = fields.One2many('student.assessment.lines', 'student_assessment_id', string="Student Assessment Lines")


    # @api.onchange('registred_sub_tags')
    # def onchange_subject_tags(self):
    #     res = {}
    #     ca_list = []
    #     sl_pool = self.env['subject.line']
    #     assessment_obj = self.env['op.assessment']
    #     assessment_master_obj = self.env['op.assessment.master']
    #     if self.registred_sub_tags:
    #         subject_lines_ids = sl_pool.search([('subject_tags','=', self.registred_sub_tags.id)])
    #         for subject_lines_id in subject_lines_ids:
    #             ca_rec_ids = assessment_master_obj.search([('ap_type','=','ca')])
    #             ca_list = [ca_id.id for ca_id in ca_rec_ids]
    #             if ca_list:
    #                 assessment_ids = assessment_obj.search([('assessment_subject_id','=',subject_lines_id.id),('op_assessment_master_ids','in', ca_list)])
    #                 assessment_list = [assessment_id.op_assessment_master_ids.id for assessment_id in assessment_ids]
    #                 if assessment_list:
    #                     res = {'domain': {'assessment_type': [('id', 'in', assessment_list)]}}
    #                 else:
    #                     res = {'domain':{'assessment_type':[('id','in',[])]}}
    #     print res,'--------------res'
    #     return res

    @api.model
    def create(self, vals):
        """ Inherit create method to pass default dc_mode as Non-Returnable when dc created from SO"""
        print vals,'-------StudentAssessment----vals'
        res = super(StudentAssessment, self).create(vals)
        return res

    @api.multi
    def create_line_ca1(self, stud_assessment_line):
        assignment_sub_lines = []
        ca1 = self.env['op.assessment.master'].search([('name','=', 'Continuous Assessment 1'),('ap_type','=','ca')])
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': ca1.id,
            'obtained_marks':stud_assessment_line.ca1,
            'percentage':stud_assessment_line.ca1,
        }
        print student_assessment_vals,'------student_assessment_vals'
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),('assignment_type','=',ca1.id)])
        if student_assessment_lines:
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
        ca2 = self.env['op.assessment.master'].search([('name','=', 'Continuous Assessment 2'),('ap_type','=','ca')])
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': ca2.id,
            'obtained_marks':stud_assessment_line.ca2,
            'percentage':stud_assessment_line.ca2,
        }
        print student_assessment_vals,'------student_assessment_vals'
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),('assignment_type','=',ca2.id)])
        if student_assessment_lines:
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
        ca3 = self.env['op.assessment.master'].search([('name','=', 'Continuous Assessment 3'),('ap_type','=','ca')])
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': ca3.id,
            'obtained_marks':stud_assessment_line.ca3,
            'percentage':stud_assessment_line.ca3,
        }
        print student_assessment_vals,'------student_assessment_vals'
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),('assignment_type','=',ca3.id)])
        if student_assessment_lines:
            for student_assessment_line in student_assessment_lines:
                student_assessment_line.unlink()
        assignment_sub_lines.append([0,0, student_assessment_vals])
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                line.student_assessment_lines = assignment_sub_lines
        return True

    @api.multi
    def create_line_ca4(self, stud_assessment_line):
        ca4 = self.env['op.assessment.master'].search([('name','=', 'Continuous Assessment 4'),('ap_type','=','ca')])
        assignment_sub_lines = []
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': ca4.id,
            'obtained_marks':stud_assessment_line.ca4,
            'percentage':stud_assessment_line.ca4,
        }
        print student_assessment_vals,'------student_assessment_vals'
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),('assignment_type','=',ca4.id)])
        if student_assessment_lines:
            for student_assessment_line in student_assessment_lines:
                student_assessment_line.unlink()
        assignment_sub_lines.append([0,0, student_assessment_vals])
        for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if line.subject_id.id == self.registred_sub_tags.subject_id.id:
                line.student_assessment_lines = assignment_sub_lines
        return True



    @api.multi
    def create_line_participation(self, stud_assessment_line):
        participation = self.env['op.assessment.master'].search([('name','=', 'Participation'),('ap_type','=','ca')])
        assignment_sub_lines = []
        student_assessment_vals = {
            'student_id': stud_assessment_line.student_id.id,
            'registered_subject': self.registred_sub_tags.id,
            'assignment_type': participation.id,
            'obtained_marks':stud_assessment_line.participation,
            'percentage':stud_assessment_line.participation,
        }
        print student_assessment_vals,'------student_assessment_vals'
        student_assessment_lines = self.env['student.assessment.line.new'].search([('student_id','=',stud_assessment_line.student_id.id),('assignment_type','=',participation.id)])
        if student_assessment_lines:
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
        print exam_vals,'------student_assessment_vals'
        exam_lines_ids = self.env['exam.score.lines'].search([('student_id','=',stud_assessment_line.student_id.id)])
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
    def update_assessment(self):
        """ Funciton to create new lines for student
            assessment on garde calculation form
        """
        assessment_obj = self.env['op.assessment']
        assignment_obj = self.env['op.assignment']
        assessment_master_obj = self.env['op.assessment.master']
        sl_pool = self.env['subject.line']

        print self.student_assessment_lines,'------------student_assessment_lines'
        for stud_assessment_line in self.student_assessment_lines:
            print stud_assessment_line,'--------------inside loop ------stud_assessment_line'
            print stud_assessment_line.student_id.id, stud_assessment_line.grade_line_id.student_id.id,'-------stud_assessment_line-------grade_line_id'
            # for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
            if stud_assessment_line.student_id.id == stud_assessment_line.grade_line_id.student_id.id:
            # for line in stud_assessment_line.grade_line_id.grade_calculation_per_sem_line:
        # if self.registred_sub_tags.subject_id.id == line.subject_id.id:
                if stud_assessment_line.ca1 > 0.0:
                    self.create_line_ca1(stud_assessment_line)
                if stud_assessment_line.ca2 > 0.0:
                    self.create_line_ca2(stud_assessment_line)
                if stud_assessment_line.ca3 > 0.0:
                    self.create_line_ca3(stud_assessment_line)
                if stud_assessment_line.ca4 > 0.0:
                    self.create_line_ca4(stud_assessment_line)
                if stud_assessment_line.participation > 0.0:
                    self.create_line_participation(stud_assessment_line)
                if stud_assessment_line.exam_score > 0.0:
                    self.create_line_exam_score(stud_assessment_line)

        # kjkdjslfkdkkkk
        return True



    ## Old logic to update assignment lines
    # @api.multi
    # def update_assessment(self):
    #     assessment_obj = self.env['op.assessment']
    #     assignment_obj = self.env['op.assignment']
    #     assessment_master_obj = self.env['op.assessment.master']
    #     sl_pool = self.env['subject.line']
    #     assignment_sub_lines = []
    #     print self.student_assessment_lines,'------------student_assessment_lines'
    #
    #
    #     for rec in self.student_assessment_lines:
    #         print rec.student_id, rec.course_reg_id.course_id,'---------course_id'
    #         subject_line_ids = sl_pool.search([('subject_id','=',self.registred_sub_tags.subject_id.id),('course_id','=',rec.course_reg_id.course_id.id),('batch_id','=',rec.course_reg_id.semester_id.id)])
    #         print subject_line_ids,'---------subject_line_ids'
    #         subject_line_ids = [line_id.id for line_id in subject_line_ids]
    #         print subject_line_ids,'-------subject_line_ids'
    #         assignment_ids = assignment_obj.search([('course_id','=',rec.course_reg_id.course_id.id),('batch_id','=',rec.course_reg_id.semester_id.id),('subject_line_id','in',subject_line_ids),('assignment_type','=',self.assessment_type.id)])
    #         print assignment_ids,'--------assessment_ids'
    #         for assignment_id in assignment_ids:
    #             print assignment_id.assignment_sub_line,'-----------assignment_sub_line'
    #             for line in assignment_id.assignment_sub_line:
    #                 if rec.student_id.id == line.student_id.id and rec.obtain_marks:
    #                     line.obtain_marks = rec.obtain_marks
    #                 else:
    #                     print '---------create records for assignment lines on grade calculation lines directly'
    #                 # assignment_sub_lines.append(line)
    #     # if assignment_sub_lines:
    #
    #     # kjkdjslfkdkkkk
    #     return True

    # @api.onchange('assessment_type')
    # def onchange_assessment_type(self):
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
            # print subject_line_ids,'-----------subject_line_ids'
            for subject_line_id in subject_line_ids:
                # appr_course_ids = course_obj.search([('course_id','=',subject_line_id.course_id.id),('semester_id','=',subject_line_id.batch_id.id),('state','=','approved')])
                appr_course_ids = course_obj.search([('course_id','=',subject_line_id.course_id.id),('semester_id','=',subject_line_id.batch_id.id),('state','=','approved')])
                # print appr_course_ids,'-------appr_course_ids'
                for course_id in appr_course_ids:
                    app_course_list.append(course_id)
            # print app_course_list,'---------app_course_list'
            for appr_course_id in app_course_list:
                # print appr_course_id,'--------appr_course_id'
                # grade_point_ids = gradepoint_obj.search([('student_id','=',appr_course_id.student_id.id),('course_id','=',appr_course_id.course_id.id),('semester_id','=',appr_course_id.semester_id.id)])
                grade_point_ids = gradepoint_obj.search([('student_id','=',appr_course_id.student_id.id),('course_id','=',appr_course_id.course_id.id),('semester_id','=',appr_course_id.semester_id.id)])
                print grade_point_ids,'--------grade_point_ids'
                for grade_point_id in grade_point_ids:
                    for line in grade_point_id.grade_calculation_per_sem_line:
                        #     if line.subject_id == self.registred_sub_tags.subject_id.id:
                        student_assessment_vals = {
                            'student_id': appr_course_id.student_id.id,
                            # 'exam_score': line.exam_score,
                            'attendance_score':line.attendance_score,
                            # 'total_score':line.total_score,
                            'grade_point':line.grade_point,
                            'grade_line_id':grade_point_id.id,
                            'grade':line.grade,
                            'course_reg_id': appr_course_id.id,
                        }
                    print student_assessment_vals,'------student_assessment_vals'
                    stud_list.append([0,0, student_assessment_vals])
                    print stud_list,'----------stud_list'
                    self.student_assessment_lines = stud_list

        res = {}

        return res


        # # @api.onchange('assessment_type')
        # # def onchange_assessment_type(self):
        #     sl_pool = self.env['subject.line']
        #     assessment_obj = self.env['op.assessment']
        #     assessment_master_obj = self.env['op.assessment.master']
        #     course_obj = self.env['course.registration']
        #     grade_calc_obj = self.env['op.assignment.sub.line']
        #     stud_list = []
        #     if self.registred_sub_tags:
        #         subject_line_ids = sl_pool.search([('subject_tags','=',self.registred_sub_tags.id)])
        #         for subject_line_id in subject_line_ids:
        #             # assessment_ids = assessment_obj.search([('assessment_subject_id','=',subject_line_id.id),('op_assessment_master_ids','=', self.assessment_type.id)])
        #             appr_course_ids = course_obj.search([('course_id','=',subject_line_id.course_id.id),('semester_id','=',subject_line_id.batch_id.id),('state','=','approved')])
        #             for appr_course_id in appr_course_ids:
        #                 # grade_calc_line_ids = grade_calc_obj.search([('student_id','=',appr_course_id.student_id.id)])
        #                 student_assessment_vals = {
        #                     'student_id': appr_course_id.student_id.id,
        #                     'course_reg_id': appr_course_id.id,
        #                 }
        #                 stud_list.append([0,0, student_assessment_vals])
        #                 self.student_assessment_lines = stud_list
        #     res = {}
        #
        #     return res

class StudentAssessmentLines(models.TransientModel):
    _name = 'student.assessment.lines'


    @api.depends('ca1','ca2','ca3','ca4','participation','exam_score','attendance_score')
    def _get_total_score(self):
        for rec in self:
            rec.total_score = rec.ca1 + rec.ca2 + rec.ca3 + rec.ca4 + rec.participation + rec.exam_score + rec.attendance_score


    @api.depends('total_score')
    def _get_grade_point(self):
        for rec in self:
            print rec.student_assessment_id,'----student_assessment_id'
            if rec.student_assessment_id:
                # for config_id in rec.student_assessment_id.
                subject_lines = self.env['subject.line'].search([('subject_tags','=',rec.student_assessment_id.registred_sub_tags.id)])
                print subject_lines,'--------subject_lines'
                for subject_line in subject_lines:
                    for grade_config in subject_line.gradepoint_configuration_ids:
                        print grade_config,'--------grade_config'
                        if rec.total_score >= grade_config.grade_from and rec.total_score <= grade_config.grade_to:
                            rec.grade = grade_config.grade
                            rec.grade_point = grade_config.point

            # jklsjdkaskdkk
            # # rec.grade_point =


    # @api.depends('total_score')
    # def _get_grade(self):
    #     for rec in self:
    #         rec.grade = rec.ca1 + rec.ca2 + rec.ca3 + rec.ca4 + rec.participation + rec.exam_score + rec.attendance_score


    student_id = fields.Many2one('op.student', string="Student")
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


    student_assessment_id = fields.Many2one('student.assessment', string=" Assessment Id")
    course_reg_id = fields.Many2one('course.registration', string="Course Registered")
