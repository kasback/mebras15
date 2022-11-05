# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PaiementEffetModelClient(models.Model):
    _name = 'paiement.effet.model.client'
    _description = "Modele Effet Client"

    name = fields.Char(string='Nom', required=True)
    company_id = fields.Many2one('res.company', string=u'Société',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.effet.model.client'))
    received_account = fields.Many2one('account.account', string=u'Compte: Effet Client à recevoir', required=True)
    at_bank_account = fields.Many2one('account.account', string=u"Compte: Effet à l'encaissement", required=True)
    bank_account = fields.Many2one('account.account', string=u"Compte: Banque", required=True)
    bank_journal_id = fields.Many2one('account.journal', string=u"Journal: Banque")

    post = fields.Boolean(string=u'A Poster', default=True)


class PaiementChequeModelClient(models.Model):
    _name = 'paiement.cheque.model.client'
    _description = "Modele Cheque Client"

    name = fields.Char(string='Nom', required=True)
    company_id = fields.Many2one('res.company', string=u'Société',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.cheque.model'))
    received_account = fields.Many2one('account.account', string=u'Compte: chèque en portfeuille', required=True)
    at_bank_account = fields.Many2one('account.account', string=u"Compte: chèque à l'encaissement", required=True)
    post = fields.Boolean(string=u'A Poster', default=True)


# Effet Client
class PaiementEffetClient(models.Model):
    _name = 'paiement.effet.client'
    _description = "Effet Client"
    _order = "date desc"

    name = fields.Char(string=u'Numéro', required=True, states={'payed': [('readonly', True)]})
    amount = fields.Float(string='Montant', required=True, states={'payed': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]})
    model_id = fields.Many2one('paiement.effet.model.client', string=u'Modèle Comptable',
                               required=True, states={'payed': [('readonly', True)]})
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]})
    due_date = fields.Date(string=u"Date d'échéance", required=True, states={'payed': [('readonly', True)]})
    at_bank_date = fields.Date(u'Date encaissement')
    payed_date = fields.Date(u'Date encaissé/rejet')
    note = fields.Text("Notes")
    bank_client = fields.Many2one("res.partner.bank", string="Banque client")
    client = fields.Many2one('res.partner', string='Client', required=True, states={'payed': [('readonly', True)]})
    move_line_ids = fields.One2many('account.move.line', 'effet_client_id',
                                    string=u'Lignes Comptables', states={'payed': [('readonly', True)]})
    tres_fees_ids = fields.One2many('tres.fees', 'effet_client_id', string=u'Frais Bancaires')
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse')
    paiement_record_id = fields.Many2one('paiement.record', string=u'Reçu de Paiement', ondelete='cascade',
                                         states={'payed': [('readonly', True)]})
    company_id = fields.Many2one('res.company', u'Société', required=True, default=lambda self: self.env['res.company']._company_default_get('paiement.effet.client'))
    reco_amount = fields.Float(string=u'Montant lettré')
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'Compte Analytique',
                                          states={'payed': [('readonly', True)]})
    rejete = fields.Boolean(string=u"Rejeté", copy=False, readonly=True, default=False)
    effet_origin_id = fields.Many2one('paiement.effet.client', string=u'Effet Origine', readonly=True)
    origin = fields.Char('Origine')
    state = fields.Selection([('draft', u'Brouillon'),
                              ('caisse', u'Caisse'),
                              ('caisse_centrale', u'Caisse centrale'),
                              ('received', u'Bordereau'),
                              ('at_bank', u'Encaissement'),
                              ('payed', u'Encaissé'),
                              ('cancel', u'Annulé'),
                              ('rejected', u'Rejeté'),
                              ('to_represent', u'Représenté'),
                              ('to_change', u'Changé')], 'Etat', default='draft', readonly=True, required=True)

    def unlink(self):
        for rec in self:
            move_ids = rec.move_line_ids.mapped('move_id')
            move_ids.button_cancel()
            move_ids.unlink()
        return super(PaiementEffetClient, self).unlink()

    def action_post_fees(self):
        for record in self:
            for fees in record.tres_fees_ids:
                if fees.state == 'draft':
                    fees.create_account_lines()

    def copy(self, default=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'move_line_ids': [],
            'paiement_record_id': False,
                        })
        return super(PaiementEffetClient, self).copy(default)

    @api.model
    def get_partner_account(self, part, type):
        account_id = False
        if part and part.id:
            account_id = part.property_account_receivable_id.id
        return account_id

    def action_post_entries(self):
        account_move_obj = self.env['account.move']
        for effet in self:
            journal_id = effet.journal_id.id
            analytic = False
            date = fields.Date.context_today(self)
            if effet.state == 'draft':
                date = effet.date
                account_id = self.get_partner_account(effet.client, 'client')
                if not account_id:
                    raise UserError(u'Le partenaire doit avoir un compte comptable')
                if effet.analytic_account_id:
                    analytic = effet.analytic_account_id.id
                deb_account = effet.model_id.received_account.id
                cred_account = account_id
            if effet.state == 'received':
                if effet.bordereau_id:
                    date = effet.bordereau_id.date
                deb_account = effet.model_id.at_bank_account.id
                cred_account = effet.model_id.received_account.id

            if effet.state == 'at_bank':
                date = effet.payed_date
                # deb_account = effet.journal_id.default_debit_account_id.id
                deb_account = effet.model_id.bank_account.id
                cred_account = effet.model_id.at_bank_account.id
                journal_id = effet.model_id.bank_journal_id.id

            debit_val = {
                'name': effet.name,
                'date': date,
                'date_maturity': effet.due_date,
                'ref': effet.note,
                'partner_id': effet.client.id,
                'account_id': deb_account,
                'credit': 0.0,
                'debit': effet.amount,
                'effet_client_id': effet.id,
                'journal_id': effet.journal_id.id,
                'currency_id':False
            }

            credit_val = {
                'name': effet.name,
                'date': date,
                'date_maturity': effet.due_date,
                'ref': effet.note,
                'partner_id': effet.client.id,
                'account_id': cred_account,
                'credit': effet.amount,
                'debit': 0.0,
                'effet_client_id': effet.id,
                'journal_id': effet.journal_id.id,
                'analytic_account_id': analytic,
                'currency_id':False
            }

            lines = [(0, 0, debit_val), (0, 0, credit_val)]

            move_id = account_move_obj.create({
                'journal_id': journal_id,
                'date': date,
                'ref': effet.note,
                'line_ids': lines,
                # 'type': 'entry'  # nacer
                })
            move_id.post()
        return True

    def action_caisse(self):
        for effet in self:
            if effet.model_id.post:
                self.action_post_entries()
            effet.write({'state': 'caisse'})
        return True

    def action_caisse_centrale(self):
        caisse_obj = self.env['paiement.caisse']
        for effet in self:
            caisse_id = caisse_obj.search([('caisse_centrale', '=', True)],limit=1)
            if not caisse_id:
                raise UserError(u"Vous devez créer une caisse centrale")
            effet.write({'caisse_id': caisse_id.id,'state': 'caisse_centrale'})
        return True

    def action_received(self):
        for effet in self:
            effet.write({'state': 'received'})
        return True

    def action_at_bank(self):
        for effet in self:
            if effet.model_id.post:
                self.action_post_entries()
            effet.write({'state': 'at_bank', 'at_bank_date': fields.Date.context_today(self)})
        return True

    def action_payed(self):
        for effet in self:
            if not effet.payed_date:
                payed_date = fields.Date.context_today(self)
            else:
                payed_date = effet.payed_date
            effet.write({'payed_date': payed_date})
            if effet.model_id.post:
                effet.action_post_entries()
            effet.write({'state': 'payed'})
        return True

    def action_cancel(self):
        for effet in self:
            effet.write({'state': 'cancel'})
        return True

    def action_rejected(self):
        for effet in self:
            if not effet.payed_date:
                payed_date = fields.Date.context_today(self)
            else:
                payed_date = effet.payed_date
            effet.write({'payed_date': payed_date})
            move_new_ids = []
            move_ids = effet.move_line_ids.mapped('move_id')
            for move_line in effet.move_line_ids:
                if move_line.reconciled:
                    move_line.remove_move_reconcile()
            for move in move_ids:
                move_new_ids.append(move.copy())
            for move_obj in move_new_ids:
                for line in move_obj.line_ids:
                    credit = line.credit
                    debit = line.debit
                    date = payed_date
                    line.write({'date': date, 'credit': debit, 'debit': credit})
                move_obj.post()
            lines = effet.move_line_ids.filtered(lambda x: x.account_id.user_type_id.type in ('receivable', 'payable'))
            lines. reconcile()
            effet.write({'state': 'rejected', 'rejete': True})
            effet.payed_date = fields.Date.context_today(self)
        return True

    def action_to_represent(self):
        for effet in self:
            caisse_centrale_id = self.env['paiement.caisse'].search([('caisse_centrale', '=', True)], limit=1)
            default = {'effet_origin_id': effet.id,
                       'paiement_record_id': effet.paiement_record_id.id,
                       'caisse_id': caisse_centrale_id.id,
                       'bordoreau_id': False}
            new_effet_id = effet.copy(default=default)
            new_effet_id.write({'paiement_record_id': effet.paiement_record_id.id})
            new_effet_id.action_caisse()
            new_effet_id.action_caisse_centrale()
            effet.write({'state': 'to_represent', 'name': effet.name + '/' + 'Rejete', 'rejete': True})
        res = self.env.ref('account_tres_customer.effet_form_client_view')
        return {
                    'name': 'Effets',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': [res and res.id or False],
                    'res_model': 'paiement.effet.client',
                    'context': "{}",
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'nodestroy': True,
                    'res_id': new_effet_id.id or False,
                }

    def effet_to_change(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Effet',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'effet_to_change',
            'target':'new',
        }


class PaiementChequeClient(models.Model):
    _name = 'paiement.cheque.client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Chèque Client'
    _order = "date desc"

    name = fields.Char(string=u'Numéro', required=True, states={'payed': [('readonly', True)]})
    amount = fields.Float(string=u'Montant', required=True, states={'payed': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]})
    model_id = fields.Many2one('paiement.cheque.model.client', string=u'Modèle Comptable',
                               required=True, states={'payed': [('readonly', True)]})
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]})
    due_date = fields.Date(string=u"Date d'échéance", required=True, states={'payed': [('readonly', True)]})
    at_bank_date = fields.Date(u'Date encaissement')
    payed_date = fields.Date(u'Date encaissé/rejet')
    note = fields.Text("Notes")
    bank_client = fields.Many2one("res.partner.bank", string="Banque client")
    client = fields.Many2one('res.partner', string='Client', required=True, states={'payed': [('readonly', True)]})
    move_line_ids = fields.One2many('account.move.line', 'cheque_client_id',
                                    string=u'Lignes Comptables', states={'payed': [('readonly', True)]})
    tres_fees_ids = fields.One2many('tres.fees', 'effet_client_id', string=u'Frais Bancaires')
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse')
    paiement_record_id = fields.Many2one('paiement.record', string=u'Reçu de Paiement', ondelete='cascade')
    company_id = fields.Many2one('res.company', u'Société', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.cheque.client'))
    reco_amount = fields.Float(string=u'Montant lettré')
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'Compte Analytique',
                                          states={'payed': [('readonly', True)]})
    rejete = fields.Boolean(string=u"Rejeté", copy=False, readonly=True, default=False)
    cheque_origin_id = fields.Many2one('paiement.cheque.client', string=u'Chèque Origine', readonly=True)
    origin = fields.Char('Origine')
    state = fields.Selection([('draft', u'Brouillon'),
                              ('caisse', u'Caisse'),
                              ('caisse_centrale', u'Caisse centrale'),
                              ('received', u'Bordereau'),
                              ('at_bank', u'Encaissement'),
                              ('payed', u'Encaissé'),
                              ('cancel', u'Annulé'),
                              ('rejected', u'Rejeté'),
                              ('to_represent', u'Représenté'),
                              ('to_change', u'Changé')], 'Etat', default='draft', readonly=True, required=True)

    def unlink(self):
        for rec in self:
            move_ids = rec.move_line_ids.mapped('move_id')
            move_ids.button_cancel()
            move_ids.unlink()
        return super(PaiementChequeClient, self).unlink()

    def action_post_fees(self):
        for cheque in self:
            for fees in cheque.tres_fees_ids:
                if fees.state == 'draft':
                    fees.create_account_lines()

    def copy(self, default=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'move_line_ids': [],
            'paiement_record_id': False,
        })
        return super(PaiementChequeClient, self).copy(default)

    @api.model
    def get_partner_account(self, part, type):
        account_id = False
        if part and part.id:
            account_id = part.property_account_receivable_id.id
        return account_id

    def action_post_entries(self):
        account_move_obj = self.env['account.move']
        for cheque in self:
            journal_id = cheque.journal_id
            analytic = False
            # date = fields.Date.context_today(self)
            date = datetime.now()
            if cheque.state == 'draft':
                date = cheque.date
                account_id = self.get_partner_account(cheque.client, 'client')
                if not account_id:
                    raise UserError(u'Le partenaire doit avoir un compte comptable')
                if cheque.analytic_account_id:
                    analytic = cheque.analytic_account_id.id
                deb_account = cheque.model_id.received_account.id
                cred_account = account_id
            if cheque.state == 'received':
                if cheque.bordereau_id:
                    date = cheque.bordereau_id.date
                deb_account = cheque.model_id.at_bank_account.id
                cred_account = cheque.model_id.received_account.id
            if cheque.state == 'at_bank':
                date = cheque.payed_date
                journal_id = cheque.bordereau_id.journal_id
                deb_account = journal_id.default_account_id.id
                cred_account = cheque.model_id.at_bank_account.id

            debit_val = {
                'name': cheque.name,
                'date': date,
                'date_maturity': cheque.due_date,
                'ref': cheque.note,
                'partner_id': cheque.client.id,
                'account_id': deb_account,
                'credit': 0.0,
                'debit': cheque.amount,
                'cheque_client_id': cheque.id,
                'journal_id': journal_id.id,
                'currency_id': False
            }

            credit_val = {
                'name': cheque.name,
                'date': date,
                'date_maturity': cheque.due_date,
                'ref': cheque.note,
                'partner_id': cheque.client.id,
                'account_id': cred_account,
                'credit': cheque.amount,
                'debit': 0.0,
                'cheque_client_id': cheque.id,
                'journal_id': journal_id.id,
                'analytic_account_id': analytic,
                'currency_id': False
            }

            lines = [(0, 0, debit_val), (0, 0, credit_val)]
            cheque_name = cheque.name
            if cheque.state == 'received':
                cheque_name = cheque.name + '[BORD]'
            elif cheque.state == 'at_bank':
                cheque_name = cheque.name + '[ENC]'
            elif cheque.state == 'rejected':
                cheque_name = cheque.name + '[REP]'
            move_id = account_move_obj.create({
                'journal_id': journal_id.id,
                'date': date,
                'name': cheque_name,
                'ref': cheque.note,
                # 'type': 'entry',
                'line_ids': lines,
            })
            move_id.post()
        return True

    def action_caisse(self):
        for cheque in self:
            if cheque.model_id.post:
                self.action_post_entries()
            cheque.write({'state': 'caisse'})
        return True

    def action_caisse_centrale(self):
        caisse_obj = self.env['paiement.caisse']
        for cheque in self:
            caisse_id = caisse_obj.search([('caisse_centrale', '=', True)], limit=1)
            if not caisse_id:
                raise UserError(u"Vous devez créer une caisse centrale")
            cheque.write({'caisse_id': caisse_id.id, 'state': 'caisse_centrale'})
        return True

    def action_received(self):
        self.write({'state': 'received'})
        if not self.bordereau_id:
            raise ValidationError(u'Veuillez renseigner le bordereau de chèque')
        return True

    def action_at_bank(self):
        for cheque in self:
            if self.model_id.post:
                self.action_post_entries()
            cheque.write({'state': 'at_bank', 'at_bank_date': fields.Date.context_today(self)})
        return True

    def action_payed(self):
        for cheque in self:
            if not cheque.payed_date:
                payed_date = fields.Date.context_today(self)
            else:
                payed_date = cheque.payed_date
            cheque.write({'payed_date': payed_date})
            if cheque.model_id.post:
                self.action_post_entries()
            cheque.write({'state': 'payed'})
        return True

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def create_accounting_lines(self, cheque, debit_account, credit_account):
        date = fields.Date.context_today(self)

        if not cheque.payed_date:
            payed_date = fields.Date.context_today(self)
        else:
            payed_date = cheque.payed_date
        cheque.write({'payed_date': payed_date})

        debit_val = {
            'name': cheque.name,
            'date': date,
            'date_maturity': cheque.due_date,
            'ref': cheque.note,
            'partner_id': cheque.client.id,
            'account_id': debit_account,
            'credit': 0.0,
            'debit': cheque.amount,
            'cheque_client_id': cheque.id,
            'journal_id': cheque.journal_id.id,
            'currency_id': False
        }

        credit_val = {
            'name': cheque.name,
            'date': date,
            'date_maturity': cheque.due_date,
            'ref': cheque.note,
            'partner_id': cheque.client.id,
            'account_id': credit_account,
            'credit': cheque.amount,
            'debit': 0.0,
            'cheque_client_id': cheque.id,
            'journal_id': cheque.journal_id.id,
            'analytic_account_id': False,
            'currency_id': False
        }

        lines = [(0, 0, debit_val), (0, 0, credit_val)]
        return lines

    def open_reject_wizard(self, in_relevet, date_rejet):
        # date = fields.Date.context_today(self)
        for cheque in self:
            journal_id = cheque.journal_id
            bank_acc_account = cheque.model_id.at_bank_account.id
            clt_account_id = self.get_partner_account(cheque.client, 'client')

            if not in_relevet:
                journal_id = cheque.bordereau_id.journal_id
                lines = self.create_accounting_lines(cheque, clt_account_id, bank_acc_account)
            else:
                bank_liquidity_acc = self.env.ref('l10n_maroc.1_pcg_51410000').id
                lines_bank = self.create_accounting_lines(cheque, bank_liquidity_acc, bank_acc_account)
                lines_clt = self.create_accounting_lines(cheque, clt_account_id, bank_liquidity_acc)
                lines = lines_clt + lines_bank

            cheque_name = cheque.name
            if cheque.state == 'at_bank':
                cheque_name = cheque.name + '[REJ]'

            move = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'date': date_rejet,
                'name': cheque_name,
                'ref': cheque.note,
                # 'type': 'entry',
                'line_ids': lines,
            })
            move.post()
            lines = cheque.move_line_ids.filtered(lambda x: x.account_id.user_type_id.type in ('receivable', 'payable'))
            lines.reconcile()

            cheque.write({'state': 'rejected', 'rejete': True})
            cheque.payed_date = fields.Date.context_today(self)
        return True

    def action_rejected(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'context': {'cheque': self},
            'view_mode': 'form',
            'res_model': 'rejet.cheque.wizard',
            'target': 'new',
        }

    def action_to_represent(self):
        for cheque in self:
            caisse_centrale_id = self.env['paiement.caisse'].search([('caisse_centrale', '=', True)], limit=1)
            default = {
                'name': cheque.name + '[REP]',
                'cheque_origin_id': cheque.id,
                'paiement_record_id': cheque.paiement_record_id.id,
                'caisse_id': caisse_centrale_id.id,
                'bordereau_id': False
            }
            new_cheque_id = cheque.copy(default=default)
            new_cheque_id.action_caisse()
            new_cheque_id.action_caisse_centrale()
            cheque.write({'state': 'to_represent', 'name': cheque.name + '/' + 'Rejete', 'rejete': True})
        res = self.env.ref('account_tres_customer.cheque_form_client_view')
        return {
            'name': 'Chèques',
            'view_mode': 'form',
            'view_id': [res and res.id or False],
            'res_model': 'paiement.cheque.client',
            'context': "{}",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'nodestroy': True,
            'res_id': new_cheque_id.id or False,
        }

    def cheque_to_change(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chèque',
            'view_mode': 'form',
            'res_model': 'cheque_to_change',
            'target': 'new',
        }


class PaiementOvClient(models.Model):
    _name = 'paiement.ov.client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Ov Client'
    _order = "date desc"

    name = fields.Char(string=u'Numéro', required=True, states={'payed': [('readonly', True)]})
    amount = fields.Float(string='Montant', required=True, states={'payed': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', string=u'Banque', states={'payed': [('readonly', True)]})
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]})
    payed_date = fields.Date('Date encaissment')
    due_date = fields.Date(string=u"Date d'échéance", required=True, states={'payed': [('readonly', True)]})
    note = fields.Text("Notes")
    bank_client = fields.Many2one("res.partner.bank", string="Banque client")
    client = fields.Many2one('res.partner', string='Client', required=True, states={'payed': [('readonly', True)]})
    move_line_ids = fields.One2many('account.move.line', 'ov_client_id', string=u'Lignes Comptables',
                                    states={'payed': [('readonly', True)]})
    tres_fees_ids = fields.One2many('tres.fees', 'ov_client_id', string=u'Frais Bancaires')
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse')
    paiement_record_id = fields.Many2one('paiement.record', string=u'Reçu de Paiement', ondelete='cascade')
    company_id = fields.Many2one('res.company', u'Société', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.ov.client'))
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'Compte Analytique',
                                          states={'payed': [('readonly', True)]})
    origin = fields.Char('Origine')
    state = fields.Selection([('draft', 'Brouillon'),
                              ('caisse', 'Caisse'),
                              ('caisse_centrale', 'Caisse centrale'),
                              ('done', u'Confirmé'),
                              ('cancel', u'Annulé'),
                              ('rejected', u'Rejeté')], 'Etat', default='draft', readonly=True, required=True)

    def unlink(self):
        for rec in self:
            move_ids = rec.move_line_ids.mapped('move_id')
            move_ids.button_cancel()
            move_ids.unlink()
        return super(PaiementOvClient, self).unlink()

    def action_post_fees(self):
        for record in self:
            for fees in record.tres_fees_ids:
                if fees.state == 'draft':
                    fees.create_account_lines()

    def copy(self, default=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'move_line_ids': [],
            'paiement_record_id': False,
        })
        return super(PaiementOvClient, self).copy(default)

    @api.model
    def get_partner_account(self, part, type):
        account_id = False
        if part and part.id:
            account_id = part.property_account_receivable_id.id
        return account_id

    def action_post_entries(self):
        account_move_obj = self.env['account.move']
        for ov in self:
            account_id = self.get_partner_account(ov.client, 'client')
            if not account_id:
                raise UserError(u'Le partenaire doit avoir un compte comptable')

            debit_val = {
                'name': ov.name,
                'date': ov.date,
                'date_maturity': ov.due_date,
                'ref': ov.note,
                'partner_id': ov.client.id,
                'account_id': account_id,
                'credit': ov.amount,
                'debit': 0.0,
                'ov_client_id': ov.id,
                'journal_id': ov.journal_id.id,
                'analytic_account_id': ov.analytic_account_id and ov.analytic_account_id.id or False,
                'currency_id': False
            }

            credit_val = {
                'name': ov.name,
                'date': ov.date,
                'date_maturity': ov.due_date,
                'ref': ov.note,
                'partner_id': ov.client.id,
                'account_id': ov.journal_id.default_account_id.id,
                'credit': 0.0,
                'debit': ov.amount,
                'ov_client_id': ov.id,
                'journal_id': ov.journal_id.id,
                'currency_id': False
            }

            lines = [(0, 0, debit_val), (0, 0, credit_val)]

            move_id = account_move_obj.create({
                'journal_id': ov.journal_id.id,
                'date': ov.date,
                'name': ov.name,
                'ref': ov.note,
                'line_ids': lines,
            })
            move_id.post()
        return True

    def action_caisse(self):
        for ov in self:
            self.action_post_entries()
            ov.write({'state': 'caisse'})

    def action_caisse_centrale(self):
        caisse_obj = self.env['paiement.caisse']
        for ov in self:
            caisse_id = caisse_obj.search([('caisse_centrale', '=', True)], limit=1)
            if not caisse_id:
                raise UserError(u"Vous devez créer une caisse centrale")
            ov.write({'caisse_id': caisse_id.id, 'state': 'caisse_centrale'})

    def action_done(self):
        for ov in self:
            ov.write({'state': 'done'})

    def action_cancel(self):
        for ov in self:
            ov.write({'state': 'cancel'})

    def action_rejected(self):
        for ov in self:
            move_new_ids = []
            move_ids = ov.move_line_ids.mapped('move_id')
            for move_line in ov.move_line_ids:
                if move_line.reconciled:
                    move_line.remove_move_reconcile()
            for move in move_ids:
                move_new_ids.append(move.copy())
            for move_obj in move_new_ids:
                for line in move_obj.line_ids:
                    credit = line.credit
                    debit = line.debit
                    line.write({'credit': debit, 'debit': credit})
                move_obj.post()
            lines = ov.move_line_ids.filtered(lambda x: x.account_id.user_type_id.type in ('receivable', 'payable'))
            lines.reconcile()
            ov.write({'state': 'rejected'})
            ov.payed_date = fields.Date.context_today(self)
        return True


class PaiementCashClient(models.Model):
    _name = 'paiement.cash.client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Espece Client'
    _order = "date desc"

    name = fields.Char(string=u'Numéro', required=True, states={'done': [('readonly', True)]})
    amount = fields.Float(string=u'Montant', required=True, states={'done': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', 'Banque', required=True, states={'done': [('readonly', True)]})
    date = fields.Date("Date", required=True, states={'done': [('readonly', True)]})
    note = fields.Text("Notes")
    client = fields.Many2one('res.partner', string=u'Client', required=True, states={'done': [('readonly', True)]})
    move_line_ids = fields.One2many('account.move.line', 'cash_client_id', 'Lignes comptables',
                                    states={'done': [('readonly', True)]})
    paiement_record_id = fields.Many2one('paiement.record', string=u'Reçu de paiement', ondelete='cascade')
    caisse_id = fields.Many2one('paiement.caisse', 'Caisse', states={'done': [('readonly', True)]})
    company_id = fields.Many2one('res.company', string=u'Société', required=True,
                                 states={'done': [('readonly', True)]},
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.cash.client'))
    analytic_account_id = fields.Many2one('account.analytic.account', 'Compte analytique',
                                          states={'done': [('readonly', True)]})
    origin = fields.Char('Origine')
    state = fields.Selection([('draft', 'Brouillon'),
                              ('caisse', 'Caisse'),
                              ('caisse_centrale', 'Caisse centrale'),
                              ('done', 'Confirme'),
                              ('cancel', 'Annule')], 'Etat', default='draft', readonly=True, required=True)

    def unlink(self):
        for rec in self:
            move_ids = rec.move_line_ids.mapped('move_id')
            move_ids.button_cancel()
            move_ids.unlink()
        return super(PaiementCashClient, self).unlink()

    def copy(self, default=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'move_line_ids': [],
            'paiement_record_id': False,
        })
        return super(PaiementCashClient, self).copy(default)

    @api.model
    def get_partner_account(self, part, type):
        account_id = False
        if part and part.id:
            account_id = part.property_account_receivable_id.id
        return account_id

    def action_caisse(self):
        account_move_obj = self.env['account.move']
        for cash in self:
            account_id = self.get_partner_account(cash.client, 'client')
            if not account_id:
                raise UserError(u'Le partenaire doit avoir un compte comptable')

            debit_val = {
                'name': cash.name,
                'date': cash.date,
                'ref': cash.note,
                'partner_id': cash.client.id,
                'account_id': account_id,
                'credit': cash.amount,
                'debit': 0.0,
                'cash_client_id': cash.id,
                'journal_id': cash.journal_id.id,
                'analytic_account_id': cash.analytic_account_id and cash.analytic_account_id.id or False,
                'currency_id': False
            }

            credit_val = {
                'name': cash.name,
                'date': cash.date,
                'ref': cash.note,
                'partner_id': cash.client.id,
                'account_id': cash.journal_id.default_account_id.id,
                'credit': 0.0,
                'debit': cash.amount,
                'cash_client_id': cash.id,
                'journal_id': cash.journal_id.id,
                'currency_id': False
            }
            lines = [(0, 0, debit_val), (0, 0, credit_val)]
            move_id = account_move_obj.create({
                'journal_id': cash.journal_id.id,
                'date': cash.date,
                'name': cash.name,
                'ref': cash.note,
                'line_ids': lines,
            })
            move_id.post()
            cash.write({'state': 'caisse'})

        return True

    def action_caisse_centrale(self):
        caisse_obj = self.env['paiement.caisse']
        for cash in self:
            caisse_id = caisse_obj.search([('caisse_centrale', '=', True)], limit=1)
            if not caisse_id:
                raise UserError(u"Vous devez créer une caisse centrale")
            cash.write({'caisse_id': caisse_id.id, 'state': 'caisse_centrale'})
        return True

    def action_cancel(self):
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        for cash in self:
            move_ids = []
            for line in cash.move_line_ids:
                move_ids.append(line.move_id)
            move_ids = list(set(move_ids))
            new_ids = []
            for move_id in move_ids:
                new_ids.append(account_move_obj.copy(move_id.id))
            move_objs = account_move_obj.browse(new_ids)
            for move_obj in move_objs:
                for line in move_obj.line_id:
                    credit = line.credit
                    debit = line.debit
                    account_move_line_obj.write(line.id, {'credit': debit, 'debit': credit})
            cash.write({'state': 'cancel'})
        return True

    def action_done(self):
        for cash in self:
            cash.write({'state': 'done'})
        return True


class PaiementCbClient(models.Model):
    _name = 'paiement.cb.client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'CB Client'
    _order = "date desc"

    name = fields.Char(string=u'Numéro', required=True, states={'payed': [('readonly', True)]})
    amount = fields.Float(string='Montant', required=True, states={'payed': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', string=u'Banque', states={'payed': [('readonly', True)]})
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]})
    payed_date = fields.Date('Date encaissment')
    due_date = fields.Date(string=u"Date d'échéance", required=True, states={'payed': [('readonly', True)]})
    note = fields.Text("Notes")
    bank_client = fields.Many2one("res.partner.bank", string="Banque client")
    client = fields.Many2one('res.partner', string='Client', required=True, states={'payed': [('readonly', True)]})
    move_line_ids = fields.One2many('account.move.line', 'cb_client_id', string=u'Lignes Comptables',
                                    states={'payed': [('readonly', True)]})
    tres_fees_ids = fields.One2many('tres.fees', 'cb_client_id', string=u'Frais Bancaires')
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse')
    paiement_record_id = fields.Many2one('paiement.record', string=u'Reçu de Paiement', ondelete='cascade')
    company_id = fields.Many2one('res.company', u'Société', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.ov.client'))
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'Compte Analytique',
                                          states={'payed': [('readonly', True)]})
    origin = fields.Char('Origine')
    state = fields.Selection([('draft', 'Brouillon'),
                              ('caisse', 'Caisse'),
                              ('caisse_centrale', 'Caisse centrale'),
                              ('done', u'Confirmé'),
                              ('cancel', u'Annulé'),
                              ('rejected', u'Rejeté')], 'Etat', default='draft', readonly=True, required=True)

    def unlink(self):
        for rec in self:
            move_ids = rec.move_line_ids.mapped('move_id')
            move_ids.button_cancel()
            move_ids.unlink()
        return super(PaiementCbClient, self).unlink()

    def action_post_fees(self):
        for record in self:
            for fees in record.tres_fees_ids:
                if fees.state == 'draft':
                    fees.create_account_lines()

    def copy(self, default=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'move_line_ids': [],
            'paiement_record_id': False,
        })
        return super(PaiementCbClient, self).copy(default)

    @api.model
    def get_partner_account(self, part, type):
        account_id = False
        if part and part.id:
            account_id = part.property_account_receivable_id.id
        return account_id

    def action_post_entries(self):
        account_move_obj = self.env['account.move']
        for cb in self:
            account_id = self.get_partner_account(cb.client, 'client')
            if not account_id:
                raise UserError(u'Le partenaire doit avoir un compte comptable')

            debit_val = {
                'name': cb.name,
                'date': cb.date,
                'date_maturity': cb.due_date,
                'ref': cb.note,
                'partner_id': cb.client.id,
                'account_id': account_id,
                'credit': cb.amount,
                'debit': 0.0,
                'cb_client_id': cb.id,
                'journal_id': cb.journal_id.id,
                'analytic_account_id': cb.analytic_account_id and cb.analytic_account_id.id or False,
                'currency_id': False
            }

            credit_val = {
                'name': cb.name,
                'date': cb.date,
                'date_maturity': cb.due_date,
                'ref': cb.note,
                'partner_id': cb.client.id,
                'account_id': cb.journal_id.default_account_id.id,
                'credit': 0.0,
                'debit': cb.amount,
                'cb_client_id': cb.id,
                'journal_id': cb.journal_id.id,
                'currency_id': False
            }

            lines = [(0, 0, debit_val), (0, 0, credit_val)]

            move_id = account_move_obj.create({
                'journal_id': cb.journal_id.id,
                'date': cb.date,
                'name': cb.name,
                'ref': cb.note,
                'line_ids': lines,
            })
            move_id.post()
        return True

    def action_caisse(self):
        for cb in self:
            self.action_post_entries()
            cb.write({'state': 'caisse'})

    def action_caisse_centrale(self):
        caisse_obj = self.env['paiement.caisse']
        for cb in self:
            caisse_id = caisse_obj.search([('caisse_centrale', '=', True)], limit=1)
            if not caisse_id:
                raise UserError(u"Vous devez créer une caisse centrale")
            cb.write({'caisse_id': caisse_id.id, 'state': 'caisse_centrale'})

    def action_done(self):
        for cb in self:
            cb.write({'state': 'done'})

    def action_cancel(self):
        for cb in self:
            cb.write({'state': 'cancel'})

    def action_rejected(self):
        for cb in self:
            move_new_ids = []
            move_ids = cb.move_line_ids.mapped('move_id')
            for move_line in cb.move_line_ids:
                if move_line.reconciled:
                    move_line.remove_move_reconcile()
            for move in move_ids:
                move_new_ids.append(move.copy())
            for move_obj in move_new_ids:
                for line in move_obj.line_ids:
                    credit = line.credit
                    debit = line.debit
                    line.write({'credit': debit, 'debit': credit})
                move_obj.post()
            lines = cb.move_line_ids.filtered(lambda x: x.account_id.user_type_id.type in ('receivable', 'payable'))
            lines.reconcile()
            cb.write({'state': 'rejected'})
            cb.payed_date = fields.Date.context_today(self)
        return True

    @api.constrains('amount')
    def check_price_cb(self):
        check_controle = self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.controle_cb')
        min = self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.min_prix_cb')
        if check_controle:
            if self.amount < float(min):
                error = u"Le montant du CB %s n'est pas accepeté car il est inférieur au minumum autorisé %s DH" % (
                    self.amount, min)
                raise ValidationError(error)
