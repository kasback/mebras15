# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PaiementPecModelClient(models.Model):
    _name = 'paiement.pec.model.client'
    _description = "Modele Prise en charge Client"

    name = fields.Char(string='Nom', required=True)
    company_id = fields.Many2one('res.company', string=u'Société',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.pec.model.client'))
    received_account = fields.Many2one('account.account', string=u'Compte: PES Client à recevoir', required=True)
    at_bank_account = fields.Many2one('account.account', string=u"Compte: PES à l'encaissement", required=True)
    bank_account = fields.Many2one('account.account', string=u"Compte: Banque", required=True)
    bank_journal_id = fields.Many2one('account.journal', string=u"Journal: Banque")

    post = fields.Boolean(string=u'A Poster', default=True)


class PaiementChequeClient(models.Model):
    _inherit = 'paiement.cheque.client'

    name = fields.Char(string=u'Numéro', readonly=True, required=False, states={'payed': [('readonly', True)]})

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_pec.seq_tres_customer_cheque').next_by_code('paiement.cheque.client') or ''
        res = super(PaiementChequeClient, self).create(vals)
        return res


class PaiementOvClient(models.Model):
    _inherit = 'paiement.ov.client'

    name = fields.Char(string=u'Numéro', readonly=True, required=False, states={'payed': [('readonly', True)]})

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_pec.seq_tres_customer_ov').next_by_code('paiement.ov.client') or ''
        res = super(PaiementOvClient, self).create(vals)
        return res


class PaiementEffetClient(models.Model):
    _inherit = 'paiement.effet.client'

    name = fields.Char(string=u'Numéro', readonly=True, required=False, states={'payed': [('readonly', True)]})

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_pec.seq_tres_customer_effet').next_by_code('paiement.effet.client') or ''
        res = super(PaiementEffetClient, self).create(vals)
        return res


class PaiementCbClient(models.Model):
    _inherit = 'paiement.cb.client'

    name = fields.Char(string=u'Numéro', readonly=True, required=False, states={'payed': [('readonly', True)]})

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_pec.seq_tres_customer_cb').next_by_code('paiement.cb.client') or ''
        res = super(PaiementCbClient, self).create(vals)
        return res


class PaiementCashClient(models.Model):
    _inherit = 'paiement.cash.client'

    name = fields.Char(string=u'Numéro', readonly=True, required=False, states={'payed': [('readonly', True)]})

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_pec.seq_tres_customer_cash').next_by_code('paiement.cash.client') or ''
        res = super(PaiementCashClient, self).create(vals)
        return res


class PaiementPecClient(models.Model):
    _name = 'paiement.pec.client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Pec Client'
    _order = "date desc"

    name = fields.Char(string=u'Numéro', readonly=True, states={'payed': [('readonly', True)]})
    amount = fields.Float(string='Montant', required=True, states={'payed': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]})
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]})
    payed_date = fields.Date('Date encaissment')
    due_date = fields.Date(string=u"Date d'échéance", required=True, states={'payed': [('readonly', True)]})
    note = fields.Text("Notes")
    bank_client = fields.Many2one("res.partner.bank", string="Banque client")
    client = fields.Many2one('res.partner', string='Client', required=True, states={'payed': [('readonly', True)]})
    model_id = fields.Many2one('paiement.pec.model.client', string=u'Modèle Comptable',
                               required=True, states={'payed': [('readonly', True)]})

    move_line_ids = fields.One2many('account.move.line', 'pec_client_id', string=u'Lignes Comptables',
                                    states={'payed': [('readonly', True)]})
    tres_fees_ids = fields.One2many('tres.fees', 'pec_client_id', string=u'Frais Bancaires')
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse')
    paiement_record_id = fields.Many2one('paiement.record', string=u'Reçu de Paiement', ondelete='cascade')
    company_id = fields.Many2one('res.company', u'Société', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.pec.client'))
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'Compte Analytique',
                                          states={'payed': [('readonly', True)]})
    origin = fields.Char('Origine')
    assurance_id = fields.Many2one('pec.assurance', string="Assurance")
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
        return super(PaiementPecClient, self).unlink()

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
        return super(PaiementPecClient, self).copy(default)

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_pec.seq_tres_customer_pec').next_by_code('paiement.pec.client') or ''
        res = super(PaiementPecClient, self).create(vals)
        return res

    @api.model
    def get_partner_account(self, part, type):
        account_id = False
        if part and part.id:
            account_id = part.property_account_receivable_id.id
        return account_id

    def action_post_entries(self):
        account_move_obj = self.env['account.move']
        for pec in self:
            account_id = self.get_partner_account(pec.client, 'client')
            if not account_id:
                raise UserError(u'Le partenaire doit avoir un compte comptable')

            debit_val = {
                'name': pec.name,
                'date': pec.date,
                'date_maturity': pec.due_date,
                'ref': pec.note,
                'partner_id': pec.client.id,
                'account_id': account_id,
                'credit': pec.amount,
                'debit': 0.0,
                'pec_client_id': pec.id,
                'journal_id': pec.journal_id.id,
                'analytic_account_id': pec.analytic_account_id and pec.analytic_account_id.id or False,
                'currency_id': False
            }

            credit_val = {
                'name': pec.name,
                'date': pec.date,
                'date_maturity': pec.due_date,
                'ref': pec.note,
                'partner_id': pec.client.id,
                'account_id': pec.model_id.received_account.id,
                'credit': 0.0,
                'debit': pec.amount,
                'pec_client_id': pec.id,
                'journal_id': pec.journal_id.id,
                'currency_id': False,
            }

            lines = [(0, 0, debit_val), (0, 0, credit_val)]

            # payment_id = self.env['account.payment'].create({
            #     'name': 'BNK/' + pec.name,
            #     'amount': pec.amount,
            #     'payment_type': 'inbound',
            #     'partner_type': 'customer',
            #     'date': pec.date,
            #     'journal_id': pec.journal_id.id,
            #     'partner_id': pec.client.id,
            # })
            #
            # payment_id.action_post()

            move_id = account_move_obj.create({
                'journal_id': pec.journal_id.id,
                'date': pec.date,
                'name': pec.name,
                'ref': pec.note,
                'line_ids': lines,
                # 'payment_id': payment_id.id
            })

            move_id.post()

        return True

    def action_caisse(self):
        for pec in self:
            self.action_post_entries()
            pec.write({'state': 'caisse'})

    def action_caisse_centrale(self):
        caisse_obj = self.env['paiement.caisse']
        for pec in self:
            caisse_id = caisse_obj.search([('caisse_centrale', '=', True)], limit=1)
            if not caisse_id:
                raise UserError(u"Vous devez créer une caisse centrale")
            pec.write({'caisse_id': caisse_id.id, 'state': 'caisse_centrale'})

    def action_done(self):
        for pec in self:
            pec.write({'state': 'done'})

    def action_cancel(self):
        for pec in self:
            pec.write({'state': 'cancel'})

    def action_rejected(self):
        for pec in self:
            move_new_ids = []
            move_ids = pec.move_line_ids.mapped('move_id')
            for move_line in pec.move_line_ids:
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
            lines = pec.move_line_ids.filtered(lambda x: x.account_id.user_type_id.type in ('receivable', 'payable'))
            lines.reconcile()
            pec.write({'state': 'rejected'})
            pec.payed_date = fields.Date.context_today(self)
        return True


class PecAssurance(models.Model):
    _name = 'pec.assurance'

    name = fields.Char('Nom')
