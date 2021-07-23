# -*- coding: utf-8 -*-

{
    'name': 'Quickteller Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Quickteller Implementation',
    'version': '1.0',
    'description': """Quickteller Payment Acquirer""",
    'author': 'Spantree Ltd',
    'depends': ['payment'],
    'data': [
        'views/paypal.xml',
        'views/payment_acquirer.xml',
        'views/res_config_view.xml',
        'data/paypal.xml',
    ],
    'installable': True,
}
