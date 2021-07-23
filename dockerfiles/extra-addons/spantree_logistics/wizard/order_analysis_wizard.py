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

from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import fields, models, api, _

class order_analysis_wizard(models.TransientModel):
    _name = 'order.analysis.wizard'

    start_date = fields.Datetime('Starting Date')
    end_date = fields.Datetime('End Date')
    user_id = fields.Many2one('res.users', 'User')

    @api.multi
    def get_data(self):
        data = self.read()[0]
        if self.start_date>self.end_date:
            raise except_orm(_('start date and end date give proper'),_("It is not valid''!"))
        data.update({'daily_trip': self._context.get('print_trip')})
        datas = {
            'ids': self._ids,
            'model': 'order.analysis.wizard',
            'form': data
        }
        return self.env['report'].get_action(self, 'spantree_logistics.report_order_analysis_template' , data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: