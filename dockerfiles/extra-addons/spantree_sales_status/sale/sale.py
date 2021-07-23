# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (c) 2012-TODAY Acespritech Solutions Pvt Ltd
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
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import urllib
import urllib2


class sale_order(osv.osv):
    _inherit = "sale.order"

    def send_mail_sms(self, cr, uid, ids=[], context=None):
        mail_obj = self.pool.get('mail.mail')
        pos_obj = self.pool.get('pos.order')
        so_obj = self.pool.get('sale.order')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        pos_ids = pos_obj.search(cr, uid, [('date_order', '>=', time.strftime('%Y-%m-%d 00:00:00')),
                                           ('date_order', '<=', time.strftime('%Y-%m-%d 23:59:59'))])
        pos_amount = so_amount = so_paid_amount = 0.0
        if pos_ids:
            pos_amount = sum(map(lambda a: a.amount_total, pos_obj.browse(cr, uid, pos_ids) or []))
        so_paid_ids = so_obj.search(cr, uid, [('date_order', '>=', time.strftime('%Y-%m-%d 00:00:00')),
                                              ('date_order', '<=', time.strftime('%Y-%m-%d 23:59:59')),
                                              ('invoiced', '=', True)])
        if so_paid_ids:
            so_paid_amount = sum(map(lambda a: a.amount_total, so_obj.browse(cr, uid, so_paid_ids) or []))
        so_ids = so_obj.search(cr, uid, [('date_order', '>=', time.strftime('%Y-%m-%d 00:00:00')),
                                         ('date_order', '<=', time.strftime('%Y-%m-%d 23:59:59')),
                                         ('state', 'not in', ['draft', 'sent', 'cancel'])])
        if so_ids:
            so_amount = sum(map(lambda a: a.amount_total, so_obj.browse(cr, uid, so_ids) or []))

        message = """<p>Your Total Sales Summary for : %s </p>
<p>Total from Point of Sale : %s </p>
<p>Total Sales Orders : %s </p>
<p>Total Paid from Sales Orders : %s </p>
<br/>
<p>Regards,</p>
<p>ERP System</p>""" % (time.strftime('%Y-%m-%d'), pos_amount, so_amount, so_paid_amount)
        if user.company_id and user.company_id.email:
            try:
                values = {
                    'subject': 'Regarding Sales-POS Details',
                    'body_html': message,
                    'email_to': user.company_id.email,
                    'email_from': 'noreply@localhost',
                }
                msg_id = mail_obj.create(cr, uid, values, context=context)
                mail_obj.send(cr, uid, [msg_id], context=context)
            except Exception, e:
                pass
        sms_message = """Your Total Sales Summary for : %s 
Total from Point of Sale : %s 
Total Sales Orders : %s
Total Paid from Sales Orders : %s""" % (time.strftime('%Y-%m-%d'), pos_amount, so_amount, so_paid_amount)
        if user.company_id and user.company_id.phone:
            self.sms_send(cr, uid, ids, user.company_id.phone, sms_message, context)
        return True

    def sms_send(self, cr, uid, ids, phone, message, context=None):
        if context is None:
            context = {}
        sms_obj = self.pool.get('sms.config')
        sms_ids = sms_obj.search(cr, uid, [('active', '=', True)])
        if sms_ids:
            sms_rec = sms_obj.browse(cr, uid, sms_ids[0])
            url = str(sms_rec.url).strip()
            login = str(sms_rec.login).strip()
            password = str(sms_rec.password).strip()
            params = urllib.urlencode({
                'user': login,
                'password': password,
                'sender': 'SIMS',
                'GSM': phone,
                'SMSText': message,
             })
            try:
                request = urllib2.Request(url, params)
                response = urllib2.urlopen(request)
                result = response.read()
            except Exception, e:
                pass
        return True

sale_order()
