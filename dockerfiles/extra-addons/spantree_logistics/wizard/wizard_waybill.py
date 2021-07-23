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

from openerp.exceptions import except_orm
from openerp import fields, models, api, _


class wizard_waybill(models.TransientModel):
    _name = 'wizard.waybill'

    start_date = fields.Datetime('Starting Date', required=True)
    end_date = fields.Datetime('End Date', required=True)
    driver_id = fields.Many2one('hr.employee', 'Employee', required=True)

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise except_orm(_('start date and end date give proper'),_("It is not valid''!"))

    @api.multi
    def get_data(self):
        if self.start_date > self.end_date:
            raise except_orm(_('start date and end date give proper'),_("It is not valid''!"))
        package_ids = self.env['fleet.package'].search([('date', '>=', self.start_date), ('date', '<=', self.end_date),
                                                        ('driver_id', '=', self.driver_id.id), ('state', '=', 'receive')])
        if not package_ids:
            raise except_orm(_('Selected Parameters has not package to transfer'),_("It is not valid''!"))
        data = {}
        data.update({'start_date' : self.start_date,
                     'end_date': self.end_date,
                     'package_ids':[package.id for package in package_ids],
                     'driver_id': self.driver_id.name,
                     'vehicle_id': package_ids[0].fleet_id.name,
                     'vehicle_license': package_ids[0].fleet_id.license_plate})
        datas = {
            'ids': self._ids,
            'model': 'wizard.waybill',
            'form': data
        }
        return self.env['report'].get_action(self, 'spantree_logistics.report_package_waybill_template' , data=datas)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: