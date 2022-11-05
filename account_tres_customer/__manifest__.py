# -*- coding: utf-8 -*-

{
    'name': 'Gestion avancée des paiements Client',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'description': '''
        Gestion avancée des paiements Client (Chèques/Effets/Espèces/OV/CB) et la gestion des bordereaux
    ''',
    'author': 'Andema',
    'website': 'http://www.andemaconsulting.com',
    'images': [],
    'depends': ['account',
                'l10n_maroc',
                'mail',
                'account_fiscal_period',
                'sales_team'
                ],
    'data': [
        'data/account_journal_data.xml',
        'security/account_tres_security.xml',
        'security/ir.model.access.csv',
        'report/customer_payments_report.xml',
        'report/report_configuration.xml',
        'report/customer_payments_report_wizard_view.xml',
        'report/report_bordereau.xml',
        'report/template_bordereau.xml',
        'report/payment_record_report.xml',
        'wizard/caisse_to_central.xml',
        'wizard/bordereau_pay.xml',
        'wizard/wizard_repr_change_view.xml',
        'wizard/rejet_wizards.xml',
        'views/account_tres_sequence.xml',
        'views/account_tres_data.xml',
        'views/paiement_record.xml',
        'views/res_config_view.xml',
        'views/paiement.xml',
        'views/bordereau.xml',
        'views/partner_view.xml',

    ],
    'demo': [],
    'test':[],
    'installable': True,
    'auto_install': False,
    'application': False,
}
