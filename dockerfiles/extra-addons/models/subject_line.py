# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api,fields, _

class SubjectLine(models.Model):
    _inherit = 'subject.line'

    # 'course_ids': fields.many2many('op.course', 'book_course_rel', 'op_book_id', 'op_course_id', string='Course', required=True),
    subject_tags = fields.Many2many(comodel_name='registered.subject')
