# -*- coding: utf-8 -*-
try:
    import simplejson as json
except ImportError:
    import json
import urllib
import urllib2
import werkzeug
from openerp import http, SUPERUSER_ID
from openerp.http import request


class PaystackController(http.Controller):
    _post_paystack_url = "https://api.paystack.co"
    _post_verify_url = _post_paystack_url + "/transaction/verify/"
    _post_url = _post_paystack_url + "/transaction/initialize"
    
    @http.route('/payment/paystack/verification', type='http', auth="public", methods=['POST', 'GET'])
    def paystack_payment_varification(self, **post):
        post['transaction_id'] = request.session.get("sale_transaction_id", False)
        post['transaction_sale_id'] = request.session.get("sale_last_order_id", False)
        post['status'] = False
        post["msg"] = ""
        if "reference" in post and "secret_key" in post:
            import requests as core_request
            try:
                paystack_obj = request.registry.get('payment.acquirer').browse(request.cr, 1, int(post["secret_key"]))
                
                if not paystack_obj.id:
                    return werkzeug.utils.redirect("shop/payment/validate") 
                if paystack_obj.environment == "test":
                    auth_key = paystack_obj.paystack_test_private_key
                else:
                    auth_key = paystack_obj.paystack_live_private_key
                    
                url = PaystackController._post_verify_url + post['reference']
                auth = auth_key
                headers = {"Authorization": "Bearer {0}".format(auth),
                            "Content-Type": "application/json",
                            "user-agent": "PaystackSDK - {0}".format('1.5.0')}
                resposne = core_request.get( url=url, headers=headers, timeout=80)
                response = resposne.json()
                if not response['status']:
                    post["msg"] = response["message"]
                else:
                    post['status'] = True
            except:
                return werkzeug.utils.redirect("shop/")
        request.registry['payment.transaction'].form_feedback(request.cr, SUPERUSER_ID, post, 'paystack', context=request.context)
            
        return werkzeug.utils.redirect("shop/payment/validate")

    def paystack_generate_token(self):
        import datetime
        import random, string
        x = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(6))
        x+=str(datetime.datetime.now()).replace("-","")[:8]
        return x

    @http.route("/payment/paystack/", type="http", auth="public", methods=["post"])
    def paystack_verification(self, **post):
        if "order_status_detail" in post and "currency_code" in post and "email" in post \
            and "phone" in post and "amount" in post:
            import requests as core_request
            paystack_key = "Bearer "
            base_url = request.registry.get('ir.config_parameter').get_param(request.cr, 1, 'web.base.url')
            url = PaystackController._post_url
            acquirer = request.registry.get('payment.acquirer').browse(request.cr, 1, int(post["order_status_detail"]))
            if acquirer.environment == "test":
                paystack_key += acquirer.paystack_test_private_key
            else:
                paystack_key += acquirer.paystack_live_private_key
            posting_headers = {"Authorization": paystack_key,
                        "Content-Type": "application/json",
                        "user-agent": "PaystackSDK - {0}".format('1.5.0')}
            amount = float(post["amount"])
            ord_id = request.session.get("sale_last_order_id", False)
            if ord_id:
                ord_id = request.registry.get("sale.order").search(request.cr, 1, [("id","=",ord_id)])
                ord_id = request.registry.get("sale.order").browse(request.cr, 1, ord_id[0])
                if ord_id.company_id.currency_id.name.upper() != "NGN":
                    ngn_obj = request.registry.get("res.currency").search(request.cr, 1, ['|',('active',"=",True),('active',"=",False),("name","=","NGN")])
                    ngn_obj = request.registry.get("res.currency").browse(request.cr, 1, ngn_obj[0])
                    if ngn_obj.id:
                        amount = (amount * ngn_obj.rate_silent) * 100.00
                    else:
                        amount = amount * 100.00
                else:
                    amount = amount * 100.00
            else:
                amount = amount * 100.00

            payment_references = self.paystack_generate_token()+str(post['order_status_detail'])
            posting_data = {"reference": payment_references, "amount": amount, "email": post['email'], 
                            "callback_url":base_url+"/payment/paystack/verification?secret_key={}".format(post['order_status_detail'])}
            if "channel" in post and "bill_ref" in post:
                if post['channel'] == "Invoice":
                    #try:
                    user_request_id = 1
                    if 'uid' in request.env.context:
                        user_request_id = request.env.context['uid']
                    invoice_id = request.registry.get("account.invoice").browse(request.cr, 1, int(post['bill_ref']))
                    if invoice_id.id:
                        import datetime
                        ngn_obj = invoice_id.currency_id
                        if invoice_id.currency_id.name != 'NGN':
                            ngn_obj = request.registry.get("res.currency").search(request.cr, 1, ['|',('active','=',True), ('active','=',False), ("name","=","NGN")])
                            ngn_obj = request.registry.get("res.currency").browse(request.cr, 1, ngn_obj[0])
                        inv_data = {'currency_id':invoice_id.currency_id.id,'converted_currency_id':ngn_obj.id,
                                 'name':"Invoice", 'invoice_id':invoice_id.id, "log_user_id":user_request_id, "log_timestampe":datetime.datetime.now(),
                                 'total_payment':amount, 'pending_amount':invoice_id.residual, 'rate_applied':ngn_obj.rate_silent,
                                 "ref":payment_references, "acquirer_id":acquirer.id}
                        request.env["paystack.logs"].sudo().create(inv_data)
                        posting_data['callback_url'] = base_url+"/payment/manual/verification?font_number={}".format(invoice_id.id)
                    
            
            response = core_request.post( url=url, headers=posting_headers, data=json.dumps(posting_data), timeout=80)
            response = response.json()
            if response['status']:
                return werkzeug.utils.redirect(response['data']['authorization_url'])
                
        return werkzeug.utils.redirect("shop/payment")
    
    @http.route("/payment/manual/verification", type='http', auth="public", website=True, methods=['POST', 'GET'])
    def payment_verification(self, **post):
        status = {"msg":"What you are looking is not here. Please contact administrator."}
        
        try:
            if "font_number" in post and "reference" in post:
                invoice_id = request.env['account.invoice'].search([('id','=',post['font_number'])])
                status['msg'] = "Please contact to administrator."
                if invoice_id.id:
                    log = request.env["paystack.logs"].search([('status', '=', False),('ref', '=', post['reference']), ('invoice_id','=',invoice_id.id)])
                    if log.id:
                        status['msg'] = "Please wait for the {} invoice status update.".format(invoice_id.number)
        except:
            pass
        return request.render("payment_paystack.paystack_redirect_url", {
            "status":status['msg']
        })
