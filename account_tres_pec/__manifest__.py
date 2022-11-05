# -*- coding: utf-8 -*-

{
    'name': 'Gestion avancée des paiements Client (Prise en charge)',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'description': '''
        Gestion avancée des paiements Client (Chèques/Effets/Espèces/OV/CB) et la gestion des bordereaux
    ''',
    'author': 'Andema',
    'website': 'http://www.andemaconsulting.com',
    'images': [],
    'depends': ['account',
                'account_tres_customer'
                ],
    'data': [
        'data/account_journal_data.xml',
        'data/data.xml',
        'views/account_tres_data.xml',
        'security/account_tres_security.xml',
        'security/ir.model.access.csv',
        'wizard/caisse_to_central.xml',
        'wizard/wizard_repr_change_view.xml',
        'views/paiement_record.xml',
        'views/paiement.xml',
        'views/partner_view.xml',
        'views/assurance_views.xml'
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
