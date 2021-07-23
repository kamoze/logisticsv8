##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from datetime import datetime

from openerp.report import report_sxw
from openerp.tools.translate import _
from openerp.osv import osv


class report_parking_methods(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(report_parking_methods, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
#             'get_date': self._get_date,
#             'get_time' : self._get_time,
            'time': datetime,

        })

#     def _get_time(self,start_date):
#         b_time = (datetime.strptime(start_date,"%Y-%m-%d %H:%M:%S").time())
#         return b_time
# 
#     def _get_date(self,start_date):
#         b_date = (datetime.strptime(start_date,"%Y-%m-%d %H:%M:%S").date())
#         return b_date

class report_parking(osv.AbstractModel):
    _name = 'report.spantree_logistics.report_parking_template'
    _inherit = 'report.abstract_report'
    _template = 'spantree_logistics.report_parking_template'
    _wrapped_report_class = report_parking_methods

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: