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
    _columns = {
        'msg_type': fields.selection([('sms', 'SMS'), ('email', 'Email')], string='Message Type'),
        'subject': fields.char('Subject'),
        'message': fields.text('Message'),
        'email_message': fields.text('Message'),
        'send_option': fields.selection([('group', 'Group'), ('all', 'All Customer'),
                                         ('selected', 'Selected')], string='Send Option'),
        'template_id': fields.many2one('message.template', 'Template'),
        'group_id': fields.many2one('sms.group', 'Group'),
        'customer_ids': fields.many2many('res.partner', 'rel_partner_sms_email',
                                        'wizard_id', 'partner_id', string='Customers')
    }
    _defaults = {
        'msg_type': 'sms',
        'send_option': 'group',
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

    def action_send(self, cr, uid, ids, context=None):
        sale_obj = self.pool.get('sale.order')
        sms_obj = self.pool.get('sms.config')
        partner_obj = self.pool.get('res.partner')
        mail_pool = self.pool.get('mail.mail')
        user_pool = self.pool.get('res.users')
        record = self.browse(cr, uid, ids[0])
        #send SMS
        if record.msg_type == 'sms':
            mobiles = []
            if record.send_option == 'group' and record.group_id:
                for customer in record.group_id.partner_ids:
                    if customer.mobile:
                        mobiles.append(customer.mobile)
            elif record.send_option == 'all':
                 partner_ids = partner_obj.search(cr, uid, [('customer','=',True)])
                 if partner_ids:
                    for part in partner_obj.browse(cr, uid, partner_ids):
                        if part.mobile:
                            mobiles.append(part.mobile)
            else:
                for cust in record.customer_ids:
                    if cust.mobile:
                        mobiles.append(cust.mobile)
            sms_ids = sms_obj.search(cr, uid, [('active', '=', True)])
            if sms_ids and mobiles:
                sms_rec = sms_obj.browse(cr, uid, sms_ids[0])
                url = str(sms_rec.url).strip()
                login = str(sms_rec.login).strip()
                password = str(sms_rec.password).strip()
                for mobile in mobiles:
                    params = urllib.urlencode({
                        'user': login,
                        'password': password,
                        'sender': 'OpenERP',
                        'GSM': mobile,
                        'SMSText': record.message,
                    })
                    try:
                        request = urllib2.Request(url, params)
                        response = urllib2.urlopen(request)
                        result = response.read()
                    except Exception, e:
                        pass
        #send Email
        else:
            recipient_ids = []
            if record.send_option == 'group' and record.group_id:
                for customer in record.group_id.partner_ids:
                    if customer.email:
                        recipient_ids.append(customer.id)
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
                    mail_id = mail_pool.create(cr, uid, {
                        'email_from': user.company_id.email,
                        'subject': record.subject,
                        'body_html': record.email_message,
                        'auto_delete': True,
                        'recipient_ids': [(4, id) for id in recipient_ids]
                    }, context=context)
                    #mail_pool.send(cr, uid, [mail_id], context=context)
        return {'type': 'ir.actions.act_window_close'}
