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
            count_pec_client = len(partner.pec_client_ids)
            partner.count_pec_client = count_pec_client

    count_pec_client = fields.Integer(compute='_paiements_count', string=u'Nbre des PEC')
    pec_client_ids = fields.One2many('paiement.pec.client', 'client', string=u'Prises en charges', readonly=True)
