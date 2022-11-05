# -*- coding: utf-8 -*-

{
    'name': u'Mebras -- Impression des Documents commerciaux',
    'version': '1.0',
    'summary': u'',
    'category': 'Gestion Commerciale',
    'author': 'Osisoftware',
    'website': '',
    'depends': [
        'base', 'web', 'account', 'partner_extend', 'stock', 'stock_landed_costs', 'osi_partner_dso'
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/report_invoice.xml',
        'data/data.xml',
        'views/account_move_views.xml',
        'views/stock_move_views.xml',
        'views/purchase_order_views.xml',
        'views/landed_cost_views.xml',
        'views/res_company_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
