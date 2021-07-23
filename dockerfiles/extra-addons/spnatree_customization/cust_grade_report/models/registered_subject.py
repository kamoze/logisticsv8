# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api,fields, _

class RegistredSubject(models.Model):
    _name = 'registered.subject'

    name = fields.Char(string="Tag name")
    subject_id = fields.Many2one('op.subject', string="Subject")
    year = fields.Many2one('subject.year', string="Year")
    active = fields.Boolean(string="Active")


class subjectYear(models.Model):
    _name = 'subject.year'

    name = fields.Char(string="Year")
