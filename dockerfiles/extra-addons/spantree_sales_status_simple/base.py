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
from openerp.osv import fields, osv
from openerp.tools.translate import _


class sms_config(osv.osv):
    _name = 'sms.config'
    _columns = {
        'url': fields.char('URL', size=64),
        'login': fields.char('Login', size=64),
        'password': fields.char('Password', size=64),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'url': 'http://api.infobip.com/api/v3/sendsms/plain',
        'active': True,
    }
sms_config()


class sms_group(osv.osv):
    _name = 'sms.group'
    _columns = {
        'name': fields.char('Name', size=64),
        'partner_ids': fields.many2many('res.partner', 'rel_group_partner', 'group_id', 'partner_id',
                                        string="Customers"),
        'type': fields.selection([('sms', 'SMS'), ('email', 'Email')], string='Type')
    }
    _defaults = {
        'type': 'sms',
    }
sms_group()


class message_template(osv.osv):
    _name = 'message.template'
    _columns = {
        'name': fields.char('Name', size=64),
        'type': fields.selection([('sms', 'SMS'), ('email', 'Email')], string='Type'),
        'message': fields.text('Message'),
        'email_message': fields.text('Message'),
        'subject': fields.char('Subject'),
    }
    _defaults = {
        'type': 'sms',
    }
message_template()
