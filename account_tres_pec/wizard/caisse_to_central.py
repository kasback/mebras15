# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PaiementPecClientWizard(models.TransientModel):
    _name = "paiement.pec.client.wizard"

    pec_id = fields.Many2one('paiement.pec.client', string=u'PEC', readonly=True)
    amount = fields.Float(string=u'Montant', readonly=True)
    due_date = fields.Date(string=u'Echéance', readonly=True)
    ok = fields.Boolean(u'Transférer?')
    caisse_id = fields.Many2one('caisse.to.central', 'Caisse', readonly=True)


class CaisseToCentral(models.TransientModel):
    _inherit = "caisse.to.central"
    
    pec_lines = fields.One2many('paiement.pec.client.wizard', 'caisse_id', string=u'PEC')

    @api.model
    def _partial_pec(self, pec):
        partial_pec = {
            'pec_id': pec.id,
            'amount': pec.amount,
        }
        return partial_pec

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
        if 'pec_lines' in fields:
            line = [(0, 0, self._partial_pec(m)) for m in caisse.pec_lines]
            res.update(pec_lines=line)
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
            for pec in wizard.pec_lines:
                if pec.pec_id.state == 'caisse' and pec.ok:
                    pec.pec_id.action_caisse_centrale()
            for cb in wizard.cb_lines:
                if cb.cb_id.state == 'caisse' and cb.ok:
                    cb.cb_id.action_caisse_centrale()
            for cash in wizard.cash_lines:
                if cash.cash_id.state == 'caisse' and cash.ok:
                    cash.cash_id.action_caisse_centrale()
        return {'type': 'ir.actions.act_window_close'}
