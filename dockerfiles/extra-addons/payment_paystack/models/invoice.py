import datetime
import json
import requests
import werkzeug
from openerp import api, models, fields, _
from openerp import http
from openerp.http import request
from openerp.exceptions import ValidationError
from ..controllers.main import PaystackController

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}


class PaysackInvoice(models.Model):
    _inherit = "account.invoice"

    paystack_ids = fields.One2many("paystack.logs", "invoice_id", string="Paystack Logs.", readonly=True)

    @api.multi
    def payment_paystack(self):
        print "payment_paystack called "

        for invoice in self:
            if invoice.state in ('draft', 'open'):
                if invoice.residual <= 0:
                    raise ValidationError(_('Not eligible for the payment.'))
                else:
                    currency_id, converted_currency_id = invoice.currency_id.id, invoice.currency_id.id
                    pending_amount, rate_applied = invoice.residual, 1
                    total_payment = 0.0
                    paystack_key = "Bearer "
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    url = PaystackController._post_url
                    acquirer = self.env['payment.acquirer'].sudo().search([('company_id', '=', invoice.company_id.id),
                                                                           ('provider', '=', 'paystack')])
                    if not acquirer.id:
                        raise ValidationError(_('Please contact Administrator to configure Paystack payment gateway.'))
                    if acquirer.environment == "test":
                        paystack_key += acquirer.paystack_test_private_key
                    else:
                        paystack_key += acquirer.paystack_live_private_key
                    posting_headers = {"Authorization": paystack_key,
                                       "Content-Type": "application/json",
                                       "user-agent": "PaystackSDK - {0}".format('1.5.0')}
                    amount = invoice.residual
                    if invoice.currency_id.name != "NGN":
                        ngn_obj = self.env["res.currency"].sudo().search(
                            ["|", ("active", "=", False), ("active", "=", True), ("name", "=", "NGN")])
                        if ngn_obj.id:
                            converted_currency_id = ngn_obj.id
                            rate_applied = ngn_obj.rate
                            amount = (amount * ngn_obj.rate) * 100.00
                        else:
                            amount = (amount * ngn_obj.rate) * 100.00
                    else:
                        amount = amount * 100.00
                PC = PaystackController()
                total_payment = amount
                posting_data = {"reference": PC.paystack_generate_token() + str(acquirer.id), "amount": amount,
                                "email": invoice.partner_id.email,
                                "callback_url": base_url + "/payment/manual/verification?font_number={}".format(
                                    invoice.id)}
                response = requests.post(url=url, headers=posting_headers, data=json.dumps(posting_data), timeout=80)
                response = response.json()
                ref = posting_data['reference']
                acquirer_id = acquirer.id

                if response['status']:
                    paystack_id = self.env['paystack.logs'].sudo().create(
                        {'currency_id': currency_id, 'converted_currency_id': converted_currency_id,
                         'name': "Invoice", 'invoice_id': invoice.id, "log_user_id": self._uid,
                         "log_timestampe": datetime.datetime.now(),
                         'total_payment': total_payment, 'pending_amount': pending_amount, 'rate_applied': rate_applied,
                         "ref": ref, "acquirer_id": acquirer_id})
                    # return response['data']['authorization_url']
                    # return werkzeug.utils.redirect(str(response['data']['authorization_url']))
                    return {
                        'type': 'ir.actions.act_url',
                        'url': response['data']['authorization_url'],
                        'target': 'new',
                        'res_id': invoice.id,
                        'paystack_id': paystack_id.id
                    }
                    return request.render(response['data']['authorization_url'], {})
                else:
                    raise ValidationError(_("{}".format(response['message'])))
            else:
                raise ValidationError(_('Not eligible for the payment.'))
        return True


PaysackInvoice()


class PaystackHistory(models.Model):
    _name = "paystack.logs"
    _order = "id desc"

    name = fields.Char(string="Channel", readonly=True, size=100)
    invoice_id = fields.Many2one("account.invoice", string="Invoice", readonly=True)
    order_id = fields.Many2one("sale.order", string="Order", readonly=True)
    status = fields.Boolean(string="Status", default=False, readonly=True)
    log_timestampe = fields.Datetime(string="Log Date", default=datetime.datetime.now(), readonly=True)
    log_user_id = fields.Many2one("res.users", string="Log User", readonly=True, default=lambda self: self.env.user)
    currency_id = fields.Many2one("res.currency", string="Actual Currency", readonly=True)
    converted_currency_id = fields.Many2one("res.currency", string="Converted Currency", readonly=True)
    rate_applied = fields.Float(string="Rate Applied", readonly=True)
    pending_amount = fields.Float(string="Pending amount", readonly=True)
    total_payment = fields.Float(string="Transaction amount", readonly=True)
    ref = fields.Char(string="Reference", readonly=True)
    acquirer_id = fields.Many2one("payment.acquirer", string="Payment method", readonly=True)
    active = fields.Boolean(string="Active", default=True, readonly=True)
    remark_by_auto_user = fields.Text(string="Description", readonly=True)

    @api.multi
    def mobile_auto_payment_check(self, mob_payment_ref):
        print "auto_payment_check called  +++++++++++++++++++++++++++", self
        for log in self.sudo().search([('invoice_id', '!=', False), ('status', '=', False)]):
            print "inside for loop"
            invoice_obj = self.env['account.invoice']
            payment_obj = self.env['account.voucher'].sudo()
            journal_obj = self.env["account.journal"]
            journal_id = self.pool.get("account.journal").search(self._cr, self._uid, [('type', '=', 'bank')],
                                                                 order="id")
            total_amount_payment = log.total_payment
            print "total_amount_payment +++++++", total_amount_payment

            if log.currency_id != log.converted_currency_id.id:
                total_amount_payment = log.total_payment / 100
            if log.invoice_id.state in ('draft', 'open'):
                if log.invoice_id.type == "out_invoice":
                    invoice_type = "out_invoice"
                    journal_type = "sale"
                    payment_type = "receipt"
                else:
                    invoice_type = "in_invoice"
                    journal_type = "purchase"
                    payment_type = "payment"
                context = {}
                context['type'] = invoice_type
                context['default_type'] = invoice_type
                context['invoice_type'] = invoice_type
                context["journal_type"] = journal_type
                context['invoice_id'] = log.invoice_id.id

                partner_id = log.invoice_id.partner_id.id
                is_multi_currency = False
                default_currency_id = log.currency_id.id
                if log.invoice_id.partner_id.parent_id:
                    partner_id = log.invoice_id.partner_id.parent_id.id
                if log.currency_id.id != log.converted_currency_id.id:
                    is_multi_currency = True
                    default_currency_id = log.converted_currency_id.id
                invoice_id = log.invoice_id

                invoice_id.with_context(context)
                defalt_payment_data = invoice_id.invoice_pay_customer()

                defalt_payment_datas = defalt_payment_data['context']
                defalt_payment_data = {
                    'payment_expected_currency': defalt_payment_datas['payment_expected_currency'],
                    'partner_id': defalt_payment_datas['default_partner_id'],
                    'amount': defalt_payment_datas['default_amount'],
                    'reference': defalt_payment_datas['default_reference'],
                    'close_after_process': defalt_payment_datas['close_after_process'],
                    'invoice_type': defalt_payment_datas['invoice_type'],
                    'invoice_id': defalt_payment_datas['invoice_id'],
                    'default_type': defalt_payment_datas['default_type'],
                    'invoice_type': defalt_payment_datas['type']}
                defalt_payment_data.update(defalt_payment_datas)
                defalt_payment_data.update(context)

                voucher_data = ["accountmobile_auto_payment_check_id", "amount", "analytic_id", "company_id", "currency_help_label",
                                "currency_id",
                                "date", "date_due", "is_multi_currency", "is_partial", "journal_id", "line_cr_ids",
                                "line_dr_ids", "line_ids",
                                "move_id", "move_ids", "name", "narration", "number", "partner_id", "pay_now",
                                "payment_option", "payment_rate",
                                "payment_rate_currency_id", "period_id", "pre_line", "reference", "state",
                                "tax_amount",
                                "tax_id", "type"]

                # def onchange_amount(cr, uid, [], amount, payment_rate, partner_id, journal_id, currency_id, type, date, payment_rate_currency_id, company_id, {'line_type':False}):
                payment_obj = payment_obj.with_context(defalt_payment_data)
                voucher_val = payment_obj.default_get(voucher_data)

                voucher_vals = defalt_payment_data
                voucher_vals.update(voucher_val)
                voucher_vals.update({'type': payment_type})
                vir_payment_id = payment_obj.new(voucher_vals)

                partner_change = vir_payment_id.sudo().onchange_partner_id(partner_id, journal_id[0], total_amount_payment,
                                                                    default_currency_id, payment_type,
                                                                    datetime.datetime.now().date())
                temp_journal_ = vir_payment_id.sudo().onchange_amount(total_amount_payment, 1, partner_id, journal_id[0],
                                                               default_currency_id, payment_type,
                                                               datetime.datetime.now().date(), log.currency_id.id,
                                                               log.invoice_id.company_id.id)
                temp_journal_1 = vir_payment_id.sudo().onchange_journal(journal_id[0],
                                                                 temp_journal_['value']['line_cr_ids'],
                                                                 False, partner_id, datetime.datetime.now().date(),
                                                                 total_amount_payment, payment_type,
                                                                 log.invoice_id.company_id.id)
                temp_journal_ = vir_payment_id.sudo().onchange_amount(total_amount_payment, 1, partner_id, journal_id[0],
                                                               default_currency_id, payment_type,
                                                               datetime.datetime.now().date(), log.currency_id.id,
                                                               log.invoice_id.company_id.id)
                main_payment_data = {}
                main_payment_data.update(voucher_vals)
                main_payment_data.update(temp_journal_["value"])
                main_payment_data.update(temp_journal_1["value"])
                main_payment_data.update({"is_multi_currency": is_multi_currency, "journal_id": journal_id[0],
                                          "company_id": log.invoice_id.company_id.id})
                paystack_obj = log.acquirer_id

                if paystack_obj.environment == "test":
                    auth_key = paystack_obj.paystack_test_private_key
                else:
                    auth_key = paystack_obj.paystack_live_private_key

                url = PaystackController._post_verify_url + mob_payment_ref
                headers = {"Authorization": "Bearer {0}".format(auth_key),
                           "Content-Type": "application/json",
                           "user-agent": "PaystackSDK - {0}".format('1.5.0')}
                resposne = requests.get(url=url, headers=headers, timeout=80)
                response = resposne.json()
                if response['status'] == False:
                    log.write({'remark_by_auto_user': response['message']})
                elif response['data']['status'] == 'failed':
                    log.write({'remark_by_auto_user': response['data']['gateway_response']})
                elif response['data']['status'] == 'success':
                    cr_lines = []
                    cr_count = 0
                    dr_lines = []
                    dr_count = 0
                    try:
                        for cr in main_payment_data['line_cr_ids']:
                            tmp_cr = cr
                            if log.invoice_id.type == "out_invoice" and is_multi_currency:
                                if tmp_cr['amount'] <= 0:
                                    tmp_cr['amount'] = total_amount_payment

                            cr_lines.append((0, 0, tmp_cr))
                    except:
                        pass
                    try:
                        for dr in main_payment_data['line_dr_ids']:
                            tmp_dr = dr
                            if log.invoice_id.type == "in_invoice" and is_multi_currency:
                                if tmp_dr['amount'] <= 0:
                                    tmp_dr['amount'] = total_amount_payment

                            dr_lines.append((0, 0, tmp_dr))
                    except:
                        pass

                    if cr_lines:
                        main_payment_data['line_cr_ids'] = cr_lines
                    if dr_lines:
                        main_payment_data['line_dr_ids'] = dr_lines

                    payment_amt_id = self.env['account.voucher'].sudo().create(main_payment_data)
                    for pymnt in payment_amt_id:
                        pymnt.button_proforma_voucher()
                    log.write({'remark_by_auto_user': response['data']['gateway_response'], 'status': True})
                else:
                    log.write({'remark_by_auto_user': response['data']['gateway_response']})
            else:
                log.write({'remark_by_auto_user': "Invoice is not in Draft/Open state.", "status": True})
        return True

    def payment_paystack_vseven(self, cr, uid, context={}):
        return self.auto_payment_check(cr, uid, context)

    @api.multi
    def auto_payment_check(self):
        for log in self.search([('invoice_id', '!=', False), ('status', '=', False)]):
            invoice_obj = self.env['account.invoice']
            payment_obj = self.env['account.voucher']
            journal_obj = self.env["account.journal"]
            journal_id = self.pool.get("account.journal").search(self._cr, self._uid, [('type', '=', 'bank')],
                                                                 order="id")
            total_amount_payment = log.total_payment
            if log.currency_id != log.converted_currency_id.id:
                total_amount_payment = log.total_payment / 100
            if log.invoice_id.state in ('draft', 'open'):
                if log.invoice_id.type == "out_invoice":
                    invoice_type = "out_invoice"
                    journal_type = "sale"
                    payment_type = "receipt"
                else:
                    invoice_type = "in_invoice"
                    journal_type = "purchase"
                    payment_type = "payment"
                context = {}
                context['type'] = invoice_type
                context['default_type'] = invoice_type
                context['invoice_type'] = invoice_type
                context["journal_type"] = journal_type
                context['invoice_id'] = log.invoice_id.id

                partner_id = log.invoice_id.partner_id.id
                is_multi_currency = False
                default_currency_id = log.currency_id.id
                if log.invoice_id.partner_id.parent_id:
                    partner_id = log.invoice_id.partner_id.parent_id.id
                if log.currency_id.id != log.converted_currency_id.id:
                    is_multi_currency = True
                    default_currency_id = log.converted_currency_id.id
                invoice_id = log.invoice_id

                invoice_id.with_context(context)
                defalt_payment_data = invoice_id.invoice_pay_customer()

                defalt_payment_datas = defalt_payment_data['context']
                defalt_payment_data = {'payment_expected_currency': defalt_payment_datas['payment_expected_currency'],
                                       'partner_id': defalt_payment_datas['default_partner_id'],
                                       'amount': defalt_payment_datas['default_amount'],
                                       'reference': defalt_payment_datas['default_reference'],
                                       'close_after_process': defalt_payment_datas['close_after_process'],
                                       'invoice_type': defalt_payment_datas['invoice_type'],
                                       'invoice_id': defalt_payment_datas['invoice_id'],
                                       'default_type': defalt_payment_datas['default_type'],
                                       'invoice_type': defalt_payment_datas['type']}
                defalt_payment_data.update(defalt_payment_datas)
                defalt_payment_data.update(context)

                voucher_data = ["account_id", "amount", "analytic_id", "company_id", "currency_help_label",
                                "currency_id",
                                "date", "date_due", "is_multi_currency", "is_partial", "journal_id", "line_cr_ids",
                                "line_dr_ids", "line_ids",
                                "move_id", "move_ids", "name", "narration", "number", "partner_id", "pay_now",
                                "payment_option", "payment_rate",
                                "payment_rate_currency_id", "period_id", "pre_line", "reference", "state", "tax_amount",
                                "tax_id", "type"]

                # def onchange_amount(cr, uid, [], amount, payment_rate, partner_id, journal_id, currency_id, type, date, payment_rate_currency_id, company_id, {'line_type':False}):
                payment_obj = payment_obj.with_context(defalt_payment_data)
                voucher_val = payment_obj.default_get(voucher_data)

                voucher_vals = defalt_payment_data
                voucher_vals.update(voucher_val)
                voucher_vals.update({'type': payment_type})
                vir_payment_id = payment_obj.new(voucher_vals)

                partner_change = vir_payment_id.onchange_partner_id(partner_id, journal_id[0], total_amount_payment,
                                                                    default_currency_id, payment_type,
                                                                    datetime.datetime.now().date())
                temp_journal_ = vir_payment_id.onchange_amount(total_amount_payment, 1, partner_id, journal_id[0],
                                                               default_currency_id, payment_type,
                                                               datetime.datetime.now().date(), log.currency_id.id,
                                                               log.invoice_id.company_id.id)
                temp_journal_1 = vir_payment_id.onchange_journal(journal_id[0], temp_journal_['value']['line_cr_ids'],
                                                                 False, partner_id, datetime.datetime.now().date(),
                                                                 total_amount_payment, payment_type,
                                                                 log.invoice_id.company_id.id)
                temp_journal_ = vir_payment_id.onchange_amount(total_amount_payment, 1, partner_id, journal_id[0],
                                                               default_currency_id, payment_type,
                                                               datetime.datetime.now().date(), log.currency_id.id,
                                                               log.invoice_id.company_id.id)
                main_payment_data = {}
                main_payment_data.update(voucher_vals)
                main_payment_data.update(temp_journal_["value"])
                main_payment_data.update(temp_journal_1["value"])
                main_payment_data.update({"is_multi_currency": is_multi_currency, "journal_id": journal_id[0],
                                          "company_id": log.invoice_id.company_id.id})
                paystack_obj = log.acquirer_id

                if paystack_obj.environment == "test":
                    auth_key = paystack_obj.paystack_test_private_key
                else:
                    auth_key = paystack_obj.paystack_live_private_key

                url = PaystackController._post_verify_url + log.ref
                headers = {"Authorization": "Bearer {0}".format(auth_key),
                           "Content-Type": "application/json",
                           "user-agent": "PaystackSDK - {0}".format('1.5.0')}
                resposne = requests.get(url=url, headers=headers, timeout=80)
                response = resposne.json()
                if response['status'] == False:
                    log.write({'remark_by_auto_user': response['message']})
                elif response['data']['status'] == 'failed':
                    log.write({'remark_by_auto_user': response['data']['gateway_response']})
                elif response['data']['status'] == 'success':
                    cr_lines = []
                    cr_count = 0
                    dr_lines = []
                    dr_count = 0
                    try:
                        for cr in main_payment_data['line_cr_ids']:
                            tmp_cr = cr
                            if log.invoice_id.type == "out_invoice" and is_multi_currency:
                                if tmp_cr['amount'] <= 0:
                                    tmp_cr['amount'] = total_amount_payment

                            cr_lines.append((0, 0, tmp_cr))
                    except:
                        pass
                    try:
                        for dr in main_payment_data['line_dr_ids']:
                            tmp_dr = dr
                            if log.invoice_id.type == "in_invoice" and is_multi_currency:
                                if tmp_dr['amount'] <= 0:
                                    tmp_dr['amount'] = total_amount_payment

                            dr_lines.append((0, 0, tmp_dr))
                    except:
                        pass

                    if cr_lines:
                        main_payment_data['line_cr_ids'] = cr_lines
                    if dr_lines:
                        main_payment_data['line_dr_ids'] = dr_lines

                    payment_amt_id = self.env['account.voucher'].create(main_payment_data)
                    for pymnt in payment_amt_id:
                        pymnt.button_proforma_voucher()
                    log.write({'remark_by_auto_user': response['data']['gateway_response'], 'status': True})
                else:
                    log.write({'remark_by_auto_user': response['data']['gateway_response']})
            else:
                log.write({'remark_by_auto_user': "Invoice is not in Draft/Open state.", "status": True})
        return True


PaystackHistory()

# 
# class PaystackPopupWizard(models.TransientModel):
#     _name = "paystack.popup.wizard"
#     
#     name = fields.Char(string="Link", readonly=True, required=True, size=255)
#     
#     
# PaystackPopupWizard()
