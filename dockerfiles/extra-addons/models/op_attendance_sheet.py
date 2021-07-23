# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api,fields, _

class OpAttendanceSheet(models.Model):
    _inherit = 'op.attendance.sheet'

    subject_tag_id = fields.Many2one('registered.subject', string="Subject Tag")
