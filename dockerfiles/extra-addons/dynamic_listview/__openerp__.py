{
    'name': 'Dynamic List',
    'summary': '',
    'version': '1.0',
    'category': 'Web',
    'description': """
        Dynamic List
    """,
    'author': "truongdung.vd@gmail.com",
    'depends': ['web'],
    'data': ['views/templates.xml',
             'security/show_fields_security.xml',
             'security/ir.model.access.csv'],
    'price': 250,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'application': False,
    'qweb': ['static/src/xml/base.xml'],
    'images': [
        'static/description/module_image.png',
    ],
}
