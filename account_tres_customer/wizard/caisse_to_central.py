# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PaiementChequeClientWizard(models.TransientModel):
    _name = "paiement.cheque.client.wizard"

    cheque_id = fields.Many2one('paiement.cheque.client', string=u'Chèque', readonly=True)
    amount = fields.Float(string=u'Montant', readonly=True)
    due_date = fields.Date(string=u'Echéance', readonly=True)
    ok = fields.Boolean(u'Transférer?')
    caisse_id = fields.Many2one('caisse.to.central', 'Caisse', readonly=True)


class PaiementEffetClientWizard(models.TransientModel):
    _name = "paiement.effet.client.wizard"

    effet_id = fields.Many2one('paiement.effet.client', string=u'Effet', readonly=True)
    amount = fields.Float(string=u'Montant', readonly=True)
    due_date = fields.Date(string=u'Echéance', readonly=True)
    ok = fields.Boolean(u'Transférer?')
    caisse_id = fields.Many2one('caisse.to.central', 'Caisse', readonly=True)


class PaiementOvClientWizard(models.TransientModel):
    _name = "paiement.ov.client.wizard"

    ov_id = fields.Many2one('paiement.ov.client', string=u'OV', readonly=True)
    amount = fields.Float(string=u'Montant', readonly=True)
    due_date = fields.Date(string=u'Echéance', readonly=True)
    ok = fields.Boolean(u'Transférer?')
    caisse_id = fields.Many2one('caisse.to.central', 'Caisse', readonly=True)


class PaiementCbClientWizard(models.TransientModel):
    _name = "paiement.cb.client.wizard"

    cb_id = fields.Many2one('paiement.cb.client', string=u'CB', readonly=True)
    amount = fields.Float(string=u'Montant', readonly=True)
    due_date = fields.Date(string=u'Echéance', readonly=True)
    ok = fields.Boolean(u'Transférer?')
    caisse_id = fields.Many2one('caisse.to.central', 'Caisse', readonly=True)


class PaiementCashClientWizard(models.TransientModel):
    _name = "paiement.cash.client.wizard"

    cash_id = fields.Many2one('paiement.cash.client', string=u'Espèce', readonly=True)
    amount = fields.Float(string=u'Montant', readonly=True)
    due_date = fields.Date(string=u'Echéance', readonly=True)
    ok = fields.Boolean(u'Transférer?')
    caisse_id = fields.Many2one('caisse.to.central', 'Caisse', readonly=True)


class CaisseToCentral(models.TransientModel):
    _name = "caisse.to.central"
    
    cheque_lines = fields.One2many('paiement.cheque.client.wizard', 'caisse_id', string=u'Chèques')
    effet_lines = fields.One2many('paiement.effet.client.wizard', 'caisse_id', string=u'Effets')
    ov_lines = fields.One2many('paiement.ov.client.wizard', 'caisse_id', string=u'OV')
    cb_lines = fields.One2many('paiement.cb.client.wizard', 'caisse_id', string=u'OV')
    cash_lines = fields.One2many('paiement.cash.client.wizard', 'caisse_id', string=u'Espèces')
    total_cheque = fields.Float(string=u'Total chèques', readonly=True)
    total_effet = fields.Float(string=u'Total effets', readonly=True)

    @api.model
    def _partial_cheque(self, cheque):
        partial_cheque = {
            'cheque_id': cheque.id,
            'amount': cheque.amount,
            'due_date': cheque.due_date,
        }
        return partial_cheque

    @api.model
    def _partial_effet(self, effet):
        partial_effet = {
            'effet_id': effet.id,
            'amount': effet.amount,
            'due_date': effet.due_date,
        }
        return partial_effet

    @api.model
    def _partial_ov(self, ov):
        partial_ov = {
            'ov_id': ov.id,
            'amount': ov.amount,
        }
        return partial_ov

    @api.model
    def _partial_cb(self, cb):
        partial_cb = {
            'cb_id': cb.id,
            'amount': cb.amount,
        }
        return partial_cb

    @api.model
    def _partial_cash(self, cash):
        partial_cash = {
            'cash_id': cash.id,
            'amount': cash.amount,
        }
        return partial_cash

    @api.model
    def default_get(self, fields):
        res = super(CaisseToCentral, self).default_get(fields)
        caisse_id = self.env.context['active_id']
        caisse = self.env['paiement.caisse'].browse(caisse_id)
        if caisse.caisse_centrale == True:
            raise ValidationError(u"Vous devez seulement transférer à partir d'une caisse normale")
        if 'cheque_lines' in fields:
            line = [(0, 0, self._partial_cheque(m)) for m in caisse.cheque_lines]
            res.update(cheque_lines=line)
        if 'effet_lines' in fields:
            line = [(0, 0, self._partial_effet(m)) for m in caisse.effet_lines]
            res.update(effet_lines=line)
        if 'ov_lines' in fields:
            line = [(0, 0, self._partial_ov(m)) for m in caisse.ov_lines]
            res.update(ov_lines = line)
        if 'cb_lines' in fields:
            line = [(0, 0, self._partial_cb(m)) for m in caisse.cb_lines]
            res.update(cb_lines = line)
        if 'cash_lines' in fields:
            line = [(0, 0, self._partial_cash(m)) for m in caisse.cash_lines]
            res.update(cash_lines = line)
        if 'total_cheque' in fields:
            total=0.0
            for ch in caisse.cheque_lines:
                total += ch.amount
            res.update(total_cheque=total)
        if 'total_effet' in fields:
            total=0.0
            for eff in caisse.effet_lines:
                total += eff.amount
            res.update(total_effet=total)
        return res

    def to_central_action(self):
        for wizard in self:
            for cheque in wizard.cheque_lines:
                if cheque.cheque_id.state == 'caisse' and cheque.ok:
                    cheque.cheque_id.action_caisse_centrale()
            for effet in wizard.effet_lines:
                if effet.effet_id.state == 'caisse' and effet.ok:
                    effet.effet_id.action_caisse_centrale()
            for ov in wizard.ov_lines:
                if ov.ov_id.state == 'caisse' and ov.ok:
                    ov.ov_id.action_caisse_centrale()
            for cb in wizard.cb_lines:
                if cb.cb_id.state == 'caisse' and cb.ok:
                    cb.cb_id.action_caisse_centrale()
            for cash in wizard.cash_lines:
                if cash.cash_id.state == 'caisse' and cash.ok:
                    cash.cash_id.action_caisse_centrale()
        return {'type': 'ir.actions.act_window_close'}
