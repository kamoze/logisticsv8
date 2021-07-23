# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-TODAY Acespritech Solutions Pvt Ltd
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
from openerp import tools, SUPERUSER_ID
from openerp.tools.translate import _
import time
import urllib
import urllib2


class wizard_mass_sms_email(osv.osv_memory):
    _name = 'wizard.mass.sms.email'
    def _get_default_company(self, cr, uid, context=None):
        company_id = self.pool.get('res.users')._get_company(cr, uid, context=context)
        if not company_id:
            raise osv.except_osv(_('Error!'), _('There is no default company for the current user!'))
        return company_id
    _columns = {
        'msg_type': fields.selection([('sms', 'SMS'), ('email', 'Email')], string='Message Type'),
        'subject': fields.char('Subject'),
        'message': fields.text('Message'),
        'email_message': fields.text('Message'),
        'send_option': fields.selection([('group', 'Group'), ('all', 'All Customer'),
                                         ('selected', 'Selected')], string='Send Option'),
        'template_id': fields.many2one('message.template', 'Template'),
        'group_id': fields.many2one('sms.group', 'Group'),
        'group_ids': fields.many2many('sms.group', 'rel_group_wizard', 'wizard_id', 'group_id',
                                        string="Groups"),
        'customer_ids': fields.many2many('res.partner', 'rel_partner_sms_email',
                                        'wizard_id', 'partner_id', string='Customers'),
        'company_id': fields.many2one('res.company', 'Company'),
#         'student_ids': fields.many2many('op.student', 'rel_student_sms_email',
#                                 'wizard_id', 'student_id', string='Students') 
    }
    _defaults = {
        'msg_type': 'sms',
        'send_option': 'group',
        'company_id': _get_default_company,
        'message': """Hi {student name},

This is to inform you that the University has changed the resumption date to 13 of Feb, 2015.

Thanks

Regards,

{Company/University name}"""
    }

    def onchange_template(self, cr, uid, ids, msg_type, template_id, context=None):
        result = {'value': {'message': False, 'subject': False}}
        if not template_id:
            return result
        template = self.pool.get('message.template').browse(cr, uid, template_id)
        if msg_type == 'sms':
            result['value']['email_message'] = False
            result['value']['message'] = template.message or False
        else:
            result['value']['message'] = False
            result['value']['email_message'] = template.email_message or False
        result['value']['subject'] = template.subject or False
        return result

    def onchange_msg_type(self, cr, uid, ids, msg_type, context=None):
        result = {'value': {}, 'domain': {}}
        if not msg_type:
            return result
        result['value'].update({'template_id': False})
        result['domain'].update({'template_id': [('type', '=', msg_type)]})
        return result


    def update_mobile_number(self, cr, uid, phone):
        ph1 = phone
        if len(ph1) <= 11:
#             start_ph = ph1[0:3]
#             if not start_ph == '234':
            if  ph1[:1] == '0':
                ph1 = '234'+ph1[1:]
            else:
                ph1 = '234'+ph1
        try:
            ph1 = int(ph1)
        except Exception:
            ph1 = ph1
        return ph1

    def action_send(self, cr, uid, ids, context=None):
        sale_obj = self.pool.get('sale.order')
        sms_obj = self.pool.get('sms.config')
        sms_group_obj = self.pool.get('sms.group')
        wiz_group_obj = self.pool.get('rel.group.wizard')
        partner_obj = self.pool.get('res.partner')
        mail_pool = self.pool.get('mail.mail')
        user_pool = self.pool.get('res.users')
        record = self.browse(cr, uid, ids[0])
        #send SMS
        if record.msg_type == 'sms':
            mobiles = []
            msg = {}
            company = record.company_id.name or 'Spantree demo University'
            if record.send_option == 'group' and record.group_ids:
                for group_id in record.group_ids:
                    print"Gggggggggggggg>>>",group_id,group_id.name
                    for customer in group_id.partner_ids:
                        if customer.mobile:
                            mobiles.append(customer.mobile)
                            msg.update({customer.mobile:record.message})
                    for faculty in group_id.faculty_ids:
                        if faculty.mobile:
                            ph = self.update_mobile_number(cr, uid, faculty.mobile)
                            mobiles.append(ph)
                            msg.update({ph:record.message})
                    for parent in group_id.parent_ids:
                        if parent.guardians_phone:
                            ph = self.update_mobile_number(cr, uid, parent.guardians_phone)
                            mobiles.append(ph)
                            msg.update({ph:record.message})
                    for emp in group_id.emp_ids:
                        if emp.work_phone:
                            ph = self.update_mobile_number(cr, uid, emp.work_phone)
                            mobiles.append(ph)
                            msg.update({ph:record.message})
                    for alumni in group_id.graduate_ids:
                        if alumni.phone:
                            ph = self.update_mobile_number(cr, uid, alumni.phone)
                            mobiles.append(ph)
                            msg.update({ph:record.message})
                    if group_id.all_stud == True:
                        student_ids = group_id.all_student_ids
                    else:
                        student_ids = group_id.student_ids
                    print"stud---->>>>",student_ids
                    if student_ids:
                        for stud in student_ids:
                            data = {'Name': stud.name,
                                    'Middle Name': stud.middle_name,
                                    'Last Name': stud.last_name,
                                    'Company/UNI': company,
                                    } 
                            stud_msg1 = """Hi %(Name)s %(Middle Name)s %(Last Name)s,""" % data
                            stud_msg2 = """Regards,
        %(Company/UNI)s""" % data
                            if stud.phone:
                                ph = self.update_mobile_number(cr, uid, stud.phone)
                                mobiles.append(ph)
                                msg.update({ph:stud_msg1+record.message+stud_msg2})
    #                             print"m:::>",msg
                            else:
                                mobiles.append(stud.name)
                                msg.update({stud.name:stud_msg1+record.message+stud_msg2})

            elif record.send_option == 'all':
                 partner_ids = partner_obj.search(cr, uid, [('customer','=',True)])
                 if partner_ids:
                    for part in partner_obj.browse(cr, uid, partner_ids):
                        if part.mobile:
                            mobiles.append(part.mobile)
                            msg.update({customer.mobile:record.message})
            else:
                for cust in record.customer_ids:
                    if cust.mobile:
                        mobiles.append(cust.mobile)
                        msg.update({customer.mobile:record.message})
            sms_ids = sms_obj.search(cr, uid, [('active', '=', True)])
            if sms_ids and mobiles:
                sms_rec = sms_obj.browse(cr, uid, sms_ids[0])
                url = str(sms_rec.url).strip()
                login = str(sms_rec.login).strip()
                password = str(sms_rec.password).strip()
                for mobile in mobiles:
#                     print"mob======>>>>",mobile
                    params = urllib.urlencode({
                        'user': login,
                        'password': password,
                        'sender': 'SIMS PAU',
                        'GSM': mobile,
                        'SMSText': msg[mobile],
                    })
                    try:
                        request = urllib2.Request(url, params)
                        response = urllib2.urlopen(request)
                        result = response.read()
                    except Exception, e:
                        print"Exp",Exception
                        pass
        #send Email
        else:
            recipient_ids = []
            if record.send_option == 'group' and record.group_ids:
                for group_id in record.group_ids:
                    print"---------->",group_id
                    for customer in group_id.partner_ids:
                        print"---------->",customer,customer.email
                        if customer.email:
                            recipient_ids.append(customer.id)
#                     for emp in group_id.emp_ids:
#                         if emp.work_email:
#                             recipient_ids.append(emp.id)
            elif record.send_option == 'all':
                 partner_ids = partner_obj.search(cr, uid, [('customer','=',True)])
                 if partner_ids:
                    for part in partner_obj.browse(cr, uid, partner_ids):
                        if part.email:
                            recipient_ids.append(part.id)
            else:
                for cust in record.customer_ids:
                    if cust.email:
                        recipient_ids.append(cust.id)
            if recipient_ids:
                user = user_pool.browse(cr, uid, uid)
                if user.company_id and user.company_id.email:
                    l=[(4, id) for id in recipient_ids]
                    print"---------->",l
                    mail_id = mail_pool.create(cr, uid, {
                        'email_from': user.company_id.email,
                        'subject': record.subject,
                        'body_html': record.email_message,
                        'auto_delete': True,
                        'recipient_ids': [(4, id) for id in recipient_ids]
                    }, context=context)
                    #mail_pool.send(cr, uid, [mail_id], context=context)
        return {'type': 'ir.actions.act_window_close'}
