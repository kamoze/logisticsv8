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

from openerp import models, api, _


class report_package_waybill_template(models.AbstractModel):
    _name = 'report.spantree_logistics.report_package_waybill_template'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('spantree_logistics.report_package_waybill_template')
        docargs = {
            'doc_ids': self.env["wizard.waybill"].browse(data["ids"]),
            'doc_model': report.model,
            'docs': self,
            'data': data,
            'get_package_details': self._get_package_details,
        }
        return report_obj.render('spantree_logistics.report_package_waybill_template', docargs)

    def _get_package_details(self, package_ids):
        package_list = []
        if package_ids:
            for package in self.env['fleet.package'].browse(package_ids):
                package_list.append({
                            'package_name': package.package_name,
                            'package_desc': package.package_desc,
                            'source_loc_id': package.source_loc_id.name or '',
                            'destination_loc_id': package.dest_loc_id.name or '',
                            'package_cat_id': package.package_cat_id.name or '',
                            'delivery_date': package.delivery_date})
            return package_list

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: