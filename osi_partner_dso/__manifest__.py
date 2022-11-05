# -*- coding: utf-8 -*-

{
    "name": u"DSO Clients",
    "version": "14.0",
    "depends": ['base', 'account', 'account_reports'],
    "author": "Osisoftware",
    "summary": "",
    'website': 'http://www.osisoftware.com',
    "category": "BASE",
    "description": "",
    "init_xml": [],
    'data': [
        'crons/cron.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/res_partner_dso_views.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
