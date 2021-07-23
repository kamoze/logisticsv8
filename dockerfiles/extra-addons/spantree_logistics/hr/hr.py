# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013-Present Acespritech Solutions Pvt. Ltd. (<http://acespritech.com>).
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
##############################################################################

from openerp.osv import fields, osv, orm


class hr_employee_document(osv.osv):
    _name = 'hr.employee.document'

    _columns = {
        'employee_id': fields.many2one('hr.employee', string="Employee"),
        'name': fields.char("Name", size=256),
        'document': fields.binary('Document', filters='*.png,*.gif,*.jpg,*.pdf,*.doc,*.docx,*.jpeg')
    }


class employee_work_history(osv.osv):
    _name = "employee.work.history"

    _columns = {
        'employee_id': fields.many2one('hr.employee', string="Employee"),
        'old_company_name': fields.char('Previous Company', size=256),
        'exp_months': fields.float('Experience in Months'),
        'salary': fields.float('Salary'),
        'ref_name': fields.char('Reference Name', size=256),
        'contact_no': fields.char('Contact Number', size=32),
    }


class hr_employee(osv.osv):
    _inherit = "hr.employee"

    _columns = {
        'emp_documents': fields.one2many('hr.employee.document', 'employee_id', 'Documents'),
        'history_ids': fields.one2many('employee.work.history', 'employee_id', 'Work History'),
        'license_no': fields.char('License No.', size=128),
        # TODO: create functional field for experience to calculate from emp.history table
        'experience': fields.float('Experience')
    }


# from openerp import models, fields, api, _
# import random 
#
# 
# class hr_employee(models.Model):
#     _inherit = 'hr.employee'
# 
#     @api.model
#     def create(self, vals):
#         user_obj = self.env['res.users']
#         if vals.get('name') and vals.get('work_email'):
#             random_word = ''
#             fields_list = user_obj.fields_get()
#             default_data = user_obj.default_get(fields_list)
#             for i in range(8):
#                 random_word += random.choice('ABCDPEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz')
#             if random_word:
#                 default_data.update({'name': vals.get('name'),
#                                      'login': vals.get('work_email'),
#                                      'password': random_word})
#                 user_id = user_obj.create(default_data)
#         if user_id:
#             vals.update({'user_id': user_id.id})
#         res = super(hr_employee, self).create(vals)
#         if res and res.user_id:
#             template_id = self.env.ref('spantree_logistics.email_employee_user_activation', False)
#             if template_id:
#                 template_obj = self.pool.get('email.template')
#                 template_obj.send_mail(self._cr , self._uid, template_id.id, res.id, True, context=None)
#         return res
# 
#     @api.one
#     def get_password(self):
#         return self.user_id.password

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: