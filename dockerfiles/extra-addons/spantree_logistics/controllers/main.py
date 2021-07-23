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

import logging

import openerp
from openerp.addons.auth_signup.res_users import SignupError
from openerp.http import request
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class AuthSignupHome(openerp.addons.web.controllers.main.Home):

    def _signup_with_values(self, token, values):
        db, login, password = request.registry['res.users'].signup(request.cr, openerp.SUPERUSER_ID, values, token)
        request.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        uid = request.session.authenticate(db, login, password)
        if not uid:
            raise SignupError(_('Authentification Failed.'))
        group_id = request.registry['res.groups'].search(request.cr, openerp.SUPERUSER_ID, [('name', '=', 'Trip Passenger')])
        if group_id and group_id[0]:
            user_id = request.registry['res.users'].browse(request.cr, openerp.SUPERUSER_ID, uid)
            user_id.write({'groups_id': [(4, group_id[0])]})
            user_id.partner_id.write({'customer': True})

# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
