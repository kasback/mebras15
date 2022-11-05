# -*- coding: utf-8 -*-

{
    "name": u"Ajout de méthodes de paiements",
    "version": "1.0",
    "depends": ['account', 'l10n_maroc'],
    "author": "Andema",
    'website': 'http://www.andemaconsulting.com',
    "description": "Methode de paiament",
    "init_xml": [],
    'data': [
        'views/payement_method.xml',
        'data/payement.method.csv',
        'security/payement_method.xml',
        'security/ir.model.access.csv',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
