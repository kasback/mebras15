# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sous_total_label = fields.Char('Label Sous-total')
    taxes_sur_label = fields.Char('Label TVA')
    total_ttc_label = fields.Char('Label Total TTC')
    infos_clt = fields.Char('Informations Client')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sous_total_label = fields.Char('Label Sous-total')
    taxes_sur_label = fields.Char('Label TVA')
    total_ttc_label = fields.Char('Label Total TTC')
    infos_clt = fields.Char('Informations Client')


class AccountMove(models.Model):
    _inherit = 'account.move'

    sous_total_label = fields.Char('Label Sous-total')
    taxes_sur_label = fields.Char('Label TVA')
    total_ttc_label = fields.Char('Label Total TTC')
    infos_clt = fields.Char('Informations Client')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    num_lot_label = fields.Char('Label du Numéro de lot')
    num_art_label = fields.Char('Label du numéro d\'article')
    designation_label = fields.Char('Label de la Désignation')
    ref_label = fields.Char('Label de la référence')
    marque_label = fields.Char('Label de la marque')
    origine_label = fields.Char('Label de l\'origine')
    qty_label = fields.Char('Label de la quantité')
    serial_number_label = fields.Char('Label Numéro de série')
    date_sequence = fields.Date('Date Séquence')
