# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api,fields, _

class IndividualCA(models.TransientModel):
    _name = 'individual.ca'
    #

    @api.multi
    def update_assessment_original_rec(self,student_lines):
        return True

    ## IRINAL ONE KEEP FOR REFERANCE neefd to use this code nowwwwww
    @api.multi
    def update_assessment_rec(self,student_lines):
        assignment_obj = self.env['op.assignment.sub.line']
        print student_lines,'---------student_lines'
        cal_lines = []
        for student_line in student_lines:
            print student_line,'--id----marks-----------line info'
            ## Logic to update CA lines and append to overwrite to main CA object
            ca_vals = {
                'obtain_marks': student_line['obtain_marks'],
            }
            line_id = assignment_obj.search([('id','=',student_line['assignment_sub_line_id'])])
            print line_id,'---------line_id'
            # cal_lines.append(ca_vals)
            if line_id:
                line_id.write(ca_vals)

    @api.model
    def create(self, vals):
        """ Inherit create method to pass default dc_mode as Non-Returnable when dc created from SO"""
        student_lines = []
        print vals,'-------------valssssssss'
        res = super(IndividualCA, self).create(vals)
        if vals and 'sudent_ca_lines':
            for rec_id in vals.get('sudent_ca_lines'):
                print rec_id,'----------rec_id'
                student_lines.append(rec_id[2])
        print student_lines,'-------student_lines'
        if student_lines:
            self.update_assessment_rec(student_lines)

        # if res:
        #     res.update_assessment_original_rec()
        return res


    #update_assessment_lines
    @api.onchange('ca_type', 'subject_id')
    def onchange_ca_type(self):
        ## Define Object Here
        grade_calc_obj = self.env['op.grade.calc.line']
        subject_line_obj = self.env['subject.line']
        print self.subject_id.subject_id.id,'-----subject_id'
        grade_calc_ids = grade_calc_obj.search([('subject_id','=', self.subject_id.subject_id.id)])
        cal_lines = []
        for grade_calc_id in grade_calc_ids:
            # print grade_calc_id, grade_calc_id.gradepoint_gradecalc_id.student_id.id, grade_calc_id.gradepoint_gradecalc_id.semester_id.id, self.sem_id,'-----grade id,-----student_id,---sem-----------sem ids'
            if grade_calc_id.gradepoint_gradecalc_id.student_id.id and grade_calc_id.gradepoint_gradecalc_id.semester_id.id == self.sem_id.id:
                # print grade_calc_id.gradepoint_assignment_ids,'-------grade_calc_id.gradepoint_assignment_ids'
                # cal_lines = []
                for gradepoint_assignment_id in grade_calc_id.gradepoint_assignment_ids:
                    print gradepoint_assignment_id.assignment_id.assignment_type.id, gradepoint_assignment_id.assignment_id.assignment_type.name,'-----------assignment'
                    if gradepoint_assignment_id.assignment_id.assignment_type.id == self.ca_type.id:
                        print gradepoint_assignment_id.id,'------gradepoint_assignment_id'
                        ca_vals = {
                            'student_id': gradepoint_assignment_id.student_id.id,
                            'obtain_marks': gradepoint_assignment_id.obtain_marks,
                            'assignment_sub_line_id': gradepoint_assignment_id.id,
                        }
                        print ca_vals,'--------ca_vals'
                        ## Create Assignment wizard auto popup values
                        # self.sudent_ca_lines = [0,0,ca_vals]
                        cal_lines.append(ca_vals)
        self.sudent_ca_lines = cal_lines


    course_id = fields.Many2one('op.course', string="Course")
    session_id = fields.Many2one('op.sessions', string="Entry Session")
    sem_id = fields.Many2one('op.batch', string="Semester")
    subject_id = fields.Many2one('subject.line', string="Subject")
    ca_type = fields.Many2one('op.assessment.master', string="Assetment Type")
    sudent_ca_lines = fields.One2many('ca.student.line', 'individual_ca_id', string="Student Lines")



class CaStudentLines(models.TransientModel):
    _name = 'ca.student.line'

    @api.model
    def create(self, vals):
        """ Inherit create method to pass default dc_mode as Non-Returnable when dc created from SO"""
        print vals,'-------CaStudentLines----vals'
        res = super(CaStudentLines, self).create(vals)
        return res

    student_id = fields.Many2one('op.student', string="Student")
    obtain_marks = fields.Float(string="CA Marks")
    assignment_sub_line_id = fields.Many2one('op.assignment.sub.line',string="Sub Line")
    individual_ca_id = fields.Many2one('individual.ca', string="IndividualCA")
