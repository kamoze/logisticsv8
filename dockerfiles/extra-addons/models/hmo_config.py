from openerp.osv import fields, osv
from datetime import datetime

class hmo_config(osv.osv):
    _name = 'hmo.config'
    _columns = {
        'name': fields.char('Name'),
        'address': fields.char('Address'),
        'product_id': fields.many2one('product.product','Package'),
        'hmo_company_id': fields.many2one('res.partner','HMO Company'),
        'remark': fields.char('Remarks'),
    }
hmo_config()

class op_health(osv.osv):
    _inherit = 'op.health'
    _columns = {
        'hmo_id': fields.many2one('hmo.config','HMO'),
        'state': fields.selection([('draft','Draft'),('approved','Approved')],'Status'),
        'invoice_id': fields.many2one('account.invoice','Invoice'),

    }

    _defaults = {
        'state': 'draft',
    }


    def approve(self, cr, uid, ids, context):
        for self_brw in self.browse(cr, uid, ids):
            if not self_brw.invoice_id:
                self.create_invoice(cr, uid, ids , context)
                return self.write(cr, uid, ids, {'state':'approved'})
        return True

    def create_invoice(self, cr, uid, ids, context):
        invoice_pool = self.pool.get('account.invoice')
        for inv in self.browse(cr, uid, ids, context):
            if not inv.invoice_id:
                invoice_dict = {}
                user = inv.student_id and inv.student_id.user_id
                partner_id = user and user.partner_id and user.partner_id.id
                company_id = user and user.company_id and user.company_id.id
                date = datetime.today().date()
                onchange_partner = invoice_pool.onchange_partner_id(cr, uid, [], type='out_invoice', \
                                                                    partner_id=partner_id, context=context)
                invoice_dict.update(onchange_partner['value'])
                invoice_dict['date_invoice'] = date
                invoice_dict['partner_id'] = partner_id
                invoice_dict['company_id'] = company_id
                invoice_dict['invoice_line'] = [((0,0,{
                    'product_id': inv.hmo_id and inv.hmo_id.product_id.id,
                    'name': inv.hmo_id and inv.hmo_id.product_id.name,
                    'quantity': 1.0,
                    'price_unit': inv.hmo_id and inv.hmo_id.product_id.lst_price or 1,
                }))]
                if invoice_dict:
                    account_invoice_id = invoice_pool.create(cr, uid, invoice_dict, context=context)
                    inv.write({'invoice_id':account_invoice_id})
                    invoice_pool.signal_workflow(cr, uid, [account_invoice_id], 'invoice_open')



        return True
