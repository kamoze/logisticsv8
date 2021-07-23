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

from openerp import models, fields, api, _
from datetime import datetime, date
from openerp.exceptions import Warning
from openerp import SUPERUSER_ID


class wizard_scan_package(models.TransientModel):
    _name = 'wizard.scan.package'

    package_transferred = fields.Text(string="Package Transferred")

    @api.multi
    def make_package_transferred(self):
        package_obj = self.env['fleet.package']
        if self.package_transferred:
            for package in set([id for id in self.package_transferred.split('\n')]):
                package_id = package_obj.search([('package_barcode', '=', package)], limit=1)
                if package_id.state != 'receive':
                    continue
                package_id.write({'state':'transfer'})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: