# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Morocco - Accounting',
    'version': '1.0',
    'category': 'Accounting/Localizations/Account Charts',
    'description': """Plan comptable, Types de comptes, Taxes""",

    'author': 'Osisoftware',
    'website': 'http://www.osisoftware.com',
    'depends': ['account', 'account_tax_code'],
    'data': [
        'data/account_chart_template.xml',
        'data/account.account.type.csv',
        'data/account.group.csv',
        'data/account.account.template.csv',
        'data/property_account.xml',
        'data/account.tax.template.csv',
        'data/account.chart.template.csv',
        'data/account_chart_template_configuration_data.xml',
        'security/account_tres_security.xml',
    ],
    'demo': [
    ],
}
