# -*- coding: utf-8 -*-

{
    "name": u"Mebras: Produits et Stock",
    "version": "14.0",
    "depends": ['base', 'stock', 'sale', 'docs_commer', 'purchase_extend', 'account_move_extend'],
    "author": "Osisoftware",
    "summary": "",
    'website': '',
    "category": "",
    "description": "Ajouter des infos sup",
    "init_xml": [],
    'data': [
        'security/ir.model.access.csv',
        'views/lot_views.xml',
        'views/pa_pv_lot_views.xml',
        'views/chiffrage_views.xml',
        'views/product_views.xml',
        'views/stock_picking.xml',
        'views/sale_order_views.xml',
        'views/stock_valuation_layer_views.xml',
        'report/enem_report.xml',
        # 'report/report_templates.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
