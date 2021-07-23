# -*- coding: utf-8 -*-

{
    'name': 'Paystack Payment Acquirer',
    'category': 'Payment Acquirer',
    'summary': 'Payment Acquirer: Paystack Implementation',
    'version': '1.0',
    'description': """Paystack Payment Acquirer for Africa.

    Paystack payment gateway supports only NGN currency.""",
    'author': 'SpantreeNG',
    'depends': ["portal", "account_voucher", 'payment', "website"],
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        'views/paystack.xml',
        'views/payment_acquirer.xml',
        'views/res_config_view.xml',
        "views/success.xml"
    ],
    'installable': True,
}
