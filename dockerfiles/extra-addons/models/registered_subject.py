# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, api,fields, _

class RegistredSubject(models.Model):
    _name = 'registered.subject'

    name = fields.Char(string="Tag name")
    subject_id = fields.Many2one('op.subject', string="Subject")
    year = fields.Many2one('subject.year', string="Year")
    active = fields.Boolean(string="Active", default=True)


class subjectYear(models.Model):
    _name = 'subject.year'

    name = fields.Char(string="Year")


class ConfirmRegisteredSubject(models.Model):
    _name = 'confirm.registered.subject.active'

    @api.multi
    def multiple_active_tag(self):
        sub_tag_obj = self.env['registered.subject']
        if self._context and 'active_ids' in self._context:
            active_ids = self._context.get('active_ids')
            for active_id in sub_tag_obj.browse(active_ids):
                if not active_id.active:
                    active_id.active = True




class ConfirmRegisteredSubject(models.Model):
    _name = 'confirm.registered.subject.inactive'

    @api.multi
    def inactive_multiple_tags(self):
        sub_tag_obj = self.env['registered.subject']
        if self._context and 'active_ids' in self._context:
            active_ids = self._context.get('active_ids')
            for active_id in sub_tag_obj.browse(active_ids):
                if active_id.active:
                    active_id.active = False