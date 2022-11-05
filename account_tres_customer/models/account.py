# -*- encoding: utf-8 -*-

from odoo import models,fields

class AccountMove(models.Model):
    _inherit = "account.move"

    paiement_record_id = fields.Many2one('paiement.record', string=u'Reçu de Paiement')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    ov_client_id = fields.Many2one('paiement.ov.client', 'OV client')
    cash_client_id = fields.Many2one('paiement.cash.client', 'Cash client')
    cheque_client_id = fields.Many2one('paiement.cheque.client', 'Cheque client')
    effet_client_id = fields.Many2one('paiement.effet.client', 'Effet client')
    cb_client_id = fields.Many2one('paiement.cb.client', 'CB client')
