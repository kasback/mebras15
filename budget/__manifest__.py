# -*- coding: utf-8 -*-

{
    "name": u"Mebras: Budget",
    "version": "14.0",
    "depends": ['base', 'stock', 'sale', 'purchase', 'account', 'product_extend'],
    "author": "Osisoftware",
    "summary": "",
    'website': '',
    "category": "",
    "description": "",
    "init_xml": [],
    'data': [
        'crons/cron.xml',
        'security/ir.model.access.csv',
        'views/budget_sale_views.xml',
        'views/budget_purchase_views.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
