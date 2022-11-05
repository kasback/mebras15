# -*- coding: utf-8 -*-

{
    'name': u'Mebras -- Documents Commericaux',
    'version': '1.0',
    'summary': u'',
    'category': 'Gestion Commerciale',
    'author': 'Osisoftware',
    'website': '',
    'depends': [
        'base', 'sale', 'account', 'purchase', 'stock', 'stock_landed_costs'
    ],
    'data': [
        'views/docs_views.xml',
        'report/templates.xml',
        'report/report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
