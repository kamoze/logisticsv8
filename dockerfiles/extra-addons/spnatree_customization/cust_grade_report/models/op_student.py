# -*- coding: utf-8 -*-
#/#############################################################################
#
#    Tech-Receptives Solutions Pvt. Ltd.
#    Copyright (C) 2004-TODAY Tech-Receptives(<http://www.tech-receptives.com>).
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
#/#############################################################################

from openerp.osv import fields, osv, orm
from openerp import models, api, _
from openerp import SUPERUSER_ID

class op_student(osv.osv):

    _inherit = 'op.student'
    _order = 'last_name'

    ## Inherit name get to change student name order by last name
    def name_get(self, cr, uid, ids, context=None):
        result= []
        if not all(ids):
            return result
        for student in self.browse(cr, uid, ids, context=context):
            # name = student.name+' '+student.middle_name+' '+student.last_name
            name = student.last_name+' '+student.middle_name+' '+student.name
            result.append((student.id,name))
        return result
