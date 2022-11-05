# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ChequeClientBordereauWizard(models.TransientModel):
    _name = "cheque.client.bordereau.wizard"

    cheque_id = fields.Many2one('paiement.cheque.client', string=u'Chèque', readonly=True)
    amount = fields.Float(string=u'Montant', readonly=True)
    type = fields.Selection([('payed', 'Paye'), ('rejected', 'Rejet')], 'Type', required=True)
    bor_id = fields.Many2one('bordereau.pay','Bordereau', readonly=True)
    date = fields.Date('Date d\'encaissement', required=True, default=fields.Date.today())


class EffetClientBordereauWizard(models.TransientModel):
    _name = "effet.client.bordereau.wizard"

    effet_id = fields.Many2one('paiement.effet.client', string=u'Effet', readonly=True)
    amount = fields.Float(string=u'Montant', readonly=True)
    type = fields.Selection([('payed', 'Paye'), ('rejected', 'Rejet')], 'Type', required=True)
    bor_id = fields.Many2one('bordereau.pay', 'Bordereau', readonly=True)
    date = fields.Date('Date d\'encaissement', required=True, default=fields.Date.today())


class BordereauPay(models.TransientModel):
    _name = "bordereau.pay"
    
    cheque_lines = fields.One2many('cheque.client.bordereau.wizard', 'bor_id', 'Cheques')
    effet_lines = fields.One2many('effet.client.bordereau.wizard', 'bor_id', 'Effets')
    type = fields.Selection([('effet', 'Effet'), ('cheque', u'Chèque')], 'Type', readonly=True)

    @api.model
    def _partial_cheque(self, cheque):
        partial_cheque = {
            'cheque_id': cheque.id,
            'amount': cheque.amount,
        }
        return partial_cheque

    @api.model
    def _partial_effet(self, effet):
        partial_effet = {
            'effet_id': effet.id,
            'amount': effet.amount,
        }
        return partial_effet

    @api.model
    def default_get(self, fields):
        bor_id = self.env.context['active_id']
        res = super(BordereauPay, self).default_get(fields)
        bor = self.env['paiement.bordereau'].browse(bor_id)
        has_frais_bancaire = self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.has_frais_bancaire')
        if has_frais_bancaire:
            if not bor.tres_fees_ids:
                raise ValidationError(u"Les frais bancaires doivent être saisis!")
        if 'cheque_lines' in fields and bor.type == 'cheque':
            cheque_lines = bor.cheque_lines.filtered(lambda r: r.state == 'at_bank')
            line = [(0, 0, self._partial_cheque(m)) for m in cheque_lines]
            res.update(cheque_lines=line, type=bor.type)
        if 'effet_lines' in fields and bor.type == 'effet':
            effet_lines = bor.effet_lines.filtered(lambda r: r.state == 'at_bank')
            line = [(0, 0, self._partial_effet(m)) for m in effet_lines]
            res.update(effet_lines=line, type=bor.type)
        return res

    def pay_action(self):
        for wizard in self:
            bor_id = self.env.context['active_id']
            bor = self.env['paiement.bordereau'].browse(bor_id)
            for cheque in wizard.cheque_lines:
                test = self.env['cheque.client.bordereau.wizard'].browse(cheque.id)
                if cheque.cheque_id.state == 'at_bank' and cheque.type == 'payed':
                    cheque.cheque_id.write({'payed_date': cheque.date})
                    cheque.cheque_id.action_payed()
                    bor.date_encaissement = cheque.date
                if cheque.cheque_id.state == 'at_bank' and cheque.type == 'rejected':
                    cheque.cheque_id.write({'payed_date': cheque.date})
                    cheque.cheque_id.action_rejected()
                    bor.date_encaissement = cheque.date
            for effet in wizard.effet_lines:
                if effet.effet_id.state == 'at_bank' and effet.type == 'payed':
                    effet.effet_id.write({'payed_date': effet.date})
                    effet.effet_id.action_payed()
                    bor.date_encaissement = effet.date
                if effet.effet_id.state == 'at_bank' and effet.type == 'rejected':
                    effet.effet_id.write({'payed_date': effet.date})
                    effet.effet_id.action_rejected()
                    bor.date_encaissement = effet.date
        return {'type': 'ir.actions.act_window_close'}