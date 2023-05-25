# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Données de base de la comptabilité Marocaine',
    'version': '1.0',
    'category': 'Accounting/Localizations/Account Charts',
    'description': """Plan comptable, Types de comptes, Taxes""",
    'summary': """
        Plan comptable, Types de comptes, Taxes""",
    'author': 'Osisoftware',
    'website': 'https://osisoftware.net/',
    'depends': ['account', 'account_tax_code'],
    'data': [
        'data/account_chart_template.xml',
        'data/account.account.type.csv',
        'data/account.group.csv',
        'data/account.account.template.csv',
        'data/property_account.xml',
        'data/account.tax.template.csv',
        'data/account_chart_template_configuration_data.xml',
        'views/res_company.xml',
        'views/res_config.xml',
        'security/account_tres_security.xml',
    ],
    'demo': [
    ],
}
