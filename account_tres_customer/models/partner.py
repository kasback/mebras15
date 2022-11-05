# -*- encoding: utf-8 -*-

from odoo import models,fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    def _paiements_count(self):
        for partner in self:
            count_cheque_client = len(partner.cheque_client_ids)
            count_effet_client = len(partner.effet_client_ids)
            count_ov_client = len(partner.ov_client_ids)
            count_cb_client = len(partner.cb_client_ids)
            count_cash_client = len(partner.cash_client_ids)
            partner.count_cheque_client = count_cheque_client
            partner.count_effet_client = count_effet_client
            partner.count_ov_client = count_ov_client
            partner.count_cb_client = count_cb_client
            partner.count_cash_client = count_cash_client

    count_cheque_client = fields.Integer(compute='_paiements_count', string=u'Nbre des Chèques')
    cheque_client_ids = fields.One2many('paiement.cheque.client', 'client', string=u'Chèques', readonly=True)
    count_effet_client = fields.Integer(compute='_paiements_count', string=u'Nbre des Effets')
    effet_client_ids = fields.One2many('paiement.effet.client', 'client', string=u'Effets', readonly=True)
    count_ov_client = fields.Integer(compute='_paiements_count', string=u'Nbre des OV')
    ov_client_ids = fields.One2many('paiement.ov.client', 'client', string=u'OV', readonly=True)
    count_cb_client = fields.Integer(compute='_paiements_count', string=u'Nbre des Cb')
    cb_client_ids = fields.One2many('paiement.cb.client', 'client', string=u'CB', readonly=True)
    count_cash_client = fields.Integer(compute='_paiements_count', string=u'Nbre des espèces')
    cash_client_ids = fields.One2many('paiement.cash.client', 'client', string=u'Espèces', readonly=True)