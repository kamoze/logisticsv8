# -*- coding: utf-'8' "-*-"

import base64
try:
    import simplejson as json
except ImportError:
    import json
from openerp.osv import osv, fields


class AcquirerPaystack(osv.Model):
    _inherit = 'payment.acquirer'


    def _get_providers(self, cr, uid, context=None):
        providers = super(AcquirerPaystack, self)._get_providers(cr, uid, context=context)
        providers.append(['paystack', 'Paystack'])
        return providers

    _columns = {
        'paystack_test_public_key': fields.char(string="Test public key", size=350),
        'paystack_test_private_key': fields.char(string="Test private key", size=350),
        'paystack_live_public_key': fields.char(string="Live public key", size=350),
        'paystack_live_private_key': fields.char(string="Live private key", size=350),
    }

    def paystack_get_form_action_url(self, cr, uid, id, context=None):
        return "/payment/paystack/"


    def paystack_form_generate_values(self, cr, uid, id, partner_values, tx_values, context={}):
        paystack_tx_values = dict(tx_values)
        bill_ref = ''
        channel ='sale'
        if 'params' in context:
            if 'model' in context['params']:
                if context['params']['model'] == "account.invoice":
                    if 'id' in context['params']:
                        bill_ref=context['params']['id']
                        channel = "Invoice"
        paystack_tx_values.update({
            "channel": channel,
            "bill_ref": bill_ref,
            "order_status_ref": tx_values['reference'],
            "order_status_detail": id,
            'amount': tx_values['amount'],
            'currency_code': tx_values['currency'] and tx_values['currency'].name or '',
            'address': partner_values['address'],
            'city': partner_values['city'],
            'country': partner_values['country'] and partner_values['country'].code or '',
            'state': partner_values['state'] and (partner_values['state'].code or partner_values['state'].name) or '',
            'email': partner_values['email'],
            'zip': partner_values['zip'],
            'name': partner_values['last_name'],
            'phone': partner_values['phone']
        })
        return partner_values, paystack_tx_values

AcquirerPaystack()


class TxPaystack(osv.Model):
    _inherit = 'payment.transaction'

    _columns = {
        'paystack_txn_id': fields.char('Transaction ID'),
    }

    def _paystack_form_get_tx_from_data(self, cr, uid, data, context=None):
        return self.browse(cr, uid, data["transaction_id"])

    def _paystak_form_get_invalid_parameters(self, cr, uid, tx, data, context=None):
        invalid_parameters = []
        error_msg = None
        if not data.get("reference", False):
            error_msg = "Paystack: Reference not't received"
            invalid_parameters.append(("reference", error_msg, tx.reference))
        if not data.get("secret_key", False):
            error_msg = "Paystack: transaction acquirer not found"
            invalid_parameters.append(("reference", error_msg, tx.reference))
        if not data.get("trxref", False):
            error_msg = "Paystack: transaction reference not received."
            invalid_parameters.append(("reference", error_msg, tx.reference))
        if not data.get("transaction_id", False):
            error_msg = "Paystack: transaction id not found."
            invalid_parameters.append(("reference", error_msg, tx.reference))
        
        paystack_id = self.pool('payment.acquirer').search(cr, 1, [('id', '=', int(data.get("secret_key"))), ('provider', '=', 'paystack')])
        if not paystack_id:
            invalid_parameters.append(("reference", "Paystack: Transaction not found.", tx.reference))
        return invalid_parameters

    def _paystack_form_validate(self, cr, uid, tx, data, context=None):
        if 'trxref' in data:
            if data['status']:
                tx.write({
                    'state': 'done',
                    'paystack_txn_id': data['trxref'],
                })
                return True
            elif data["status"] == False:
                tx.write({
                    'state': 'cancel',
                    'paystack_txn_id': data['trxref'],
                })
                return True
        return False

