# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class TresFees(models.Model):
    _name = 'tres.fees'
    _description = "Frais"
    _rec_name='account_id'

    def unlink(self):
        for fee in self:
            if fee.move_id:
                raise UserError(u"L'écriture comptable liée aux frais doit être supprimée avant de procéder!")
        return super(TresFees, self).unlink()

    def create_account_lines(self):
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        res = []
        for record in self:
            journal_id = False
            date = False
            name = False
            ref = False
            partner_id = False
            if record.ov_client_id:
                journal_id = record.ov_client_id.journal_id
                date = record.ov_client_id.date
                name = record.ov_client_id.name
                ref = record.ov_client_id.note
                partner_id = record.ov_client_id.client.id

            if record.cb_client_id:
                journal_id = record.cb_client_id.journal_id
                date = record.cb_client_id.date
                name = record.cb_client_id.name
                ref = record.cb_client_id.note
                partner_id = record.cb_client_id.client.id

            if record.cheque_client_id:
                journal_id = record.cheque_client_id.journal_id
                date = record.cheque_client_id.date
                name = record.cheque_client_id.name
                ref = record.cheque_client_id.note
                partner_id = record.cheque_client_id.client.id

            if record.effet_client_id:
                journal_id = record.effet_client_id.journal_id
                date = record.effet_client_id.date
                name = record.effet_client_id.name
                ref = record.effet_client_id.note
                partner_id = record.effet_client_id.client.id

            if record.bordereau_id:
                journal_id = record.bordereau_id.journal_id
                date = record.bordereau_id.date
                name = record.bordereau_id.name
                ref = record.bordereau_id.name
                partner_id = False

            move_id = account_move_obj.create({
                'journal_id': journal_id.id,
                'date': date,
                'name': name,
            })
            debit = {
                'name': name,
                'date': date,
                'partner_id': partner_id,
                'account_id': record.account_id.id,
                'credit': 0.0,
                'debit': record.amount,
                'journal_id': journal_id.id,
            }

            # account_move_line_obj.create(debit)
            if not journal_id.default_account_id:
                raise UserError(u'Il faut lier le compte crédit au journal de la pièce')
            credit = {
                'name': name,
                'date': date,
                'partner_id': partner_id,
                'account_id': journal_id.default_account_id.id,
                'credit': record.amount,
                'debit': 0.0,
                'journal_id': journal_id.id,
            }
            move_id.write({'line_ids': [(0, 0, credit), (0, 0, debit)]})
            move_id.post()
            res.append(move_id)
            record.write({'state': 'done', 'move_id': move_id.id})
        return res

    cheque_client_id = fields.Many2one('paiement.cheque.client', string=u'Chèque client')
    ov_client_id = fields.Many2one('paiement.ov.client', string=u'OV client')
    effet_client_id = fields.Many2one('paiement.effet.client', string=u'Effet client')
    cb_client_id = fields.Many2one('paiement.cb.client', string=u'CB client')
    move_id = fields.Many2one('account.move', string=u'Ecriture comptable', readonly=True)
    amount = fields.Float('Montant', required=True)
    account_id = fields.Many2one('account.account', string=u'Compte de charge', required=True)
    company_id = fields.Many2one('res.company', string=u'Société', readonly=True, default=lambda self: self.env['res.company']._company_default_get('tres.fees'))
    state = fields.Selection([
                    ('draft', u'Brouillon'),
                    ('done', u'Validé'),], 'Etat', default='draft', readonly=True, required=True)

class ResUsers(models.Model):
    _inherit = 'res.users'

    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse')


class PaiementCaisse(models.Model):
    _name = 'paiement.caisse'
    _description = "Caisse de Paiement"
    _inherit = ['mail.thread']

    @api.depends('cheque_lines', 'effet_lines', 'ov_lines', 'cash_lines.amount')
    def _calc_total_amount(self):
        for rec in self:
            rec.nb_cheques = len(rec.cheque_lines)
            rec.nb_effets = len(rec.effet_lines)
            rec.nb_ov = len(rec.ov_lines)
            rec.nb_cb = len(rec.cb_lines)
            rec.total_amount = sum(cheque.amount for cheque in rec.cheque_lines) + sum(effet.amount for effet in rec.effet_lines)+ \
                                sum(ov.amount for ov in rec.ov_lines) + sum(cash.amount for cash in rec.cash_lines) + sum(cb.amount for cb in rec.cb_lines)

    name = fields.Char(u'Description', required=True)
    code = fields.Char(u'Code', required=True)
    caisse_centrale = fields.Boolean(string=u'Caisse centrale')
    company_id = fields.Many2one('res.company', string=u'Société', readonly=True, default=lambda self: self.env['res.company']._company_default_get('paiement.caisse'))
    cheque_lines = fields.One2many('paiement.cheque.client', 'caisse_id', string=u'Chèques', readonly=True)
    effet_lines = fields.One2many('paiement.effet.client', 'caisse_id', string=u'Effets', readonly=True)
    ov_lines = fields.One2many('paiement.ov.client', 'caisse_id', string=u'OV', readonly=True)
    cb_lines = fields.One2many('paiement.cb.client', 'caisse_id', string=u'CB', readonly=True)
    cash_lines = fields.One2many('paiement.cash.client', 'caisse_id', string=u'Espèces', readonly=True)
    total_amount = fields.Float(compute='_calc_total_amount', string=u'Montant total')
    nb_cheques = fields.Float(compute='_calc_total_amount', string=u'Nombre de chèques')
    nb_effets = fields.Float(compute='_calc_total_amount', string=u"Nombre d'effets")
    nb_ov = fields.Float(compute='_calc_total_amount', string=u"Nombre d'OV")
    nb_cb = fields.Float(compute='_calc_total_amount', string=u"Nombre de CB")


class PaiementRecord(models.Model):
    _name = "paiement.record"
    _description = "Paiement Client"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "date desc"

    @api.model
    def _default_caisse(self):
        caisse_id = self.env.user.caisse_id
        if caisse_id:
            return caisse_id.id
    # deleted this , 'invoice_ids.type' in the dependencies list below since account.move has no type anymore in odoo 14
    @api.depends('paiement_lines.amount', 'invoice_ids.amount_residual')
    def _calc_amount(self):
        for rec in self:
            rec.amount = sum(line.amount for line in rec.paiement_lines)
            rec.amount_invoices = sum(invoice.amount_residual for invoice in rec.invoice_ids if invoice.type == 'out_invoice')
            rec.amount_avoirs = sum(avoir.amount_residual for avoir in rec.invoice_ids if avoir.type == 'out_refund')
            rec.amount_diff = rec.amount + rec.amount_avoirs - rec.amount_invoices

    @api.model
    def create(self, vals):
        caisse = self.env['paiement.caisse'].browse(vals['caisse_id'])
        name = str(caisse.name).encode('utf-8').decode('utf-8')
        name += '/'+self.env['ir.sequence'].next_by_code('paiement.record')
        vals['name'] = name
        res=super(PaiementRecord, self).create(vals)
        return res

    name = fields.Char(string=u'Réference', readonly=True)
    company_id = fields.Many2one('res.company', string=u'Société', readonly=True,
                                 default=lambda self: self.env['res.company']._company_default_get('paiement.record'))
    client_id = fields.Many2one('res.partner', string=u'Client', states={'done': [('readonly', True)]}, required=True)
    user_id = fields.Many2one('res.users', string=u'Vendeur', states={'done': [('readonly', True)]})
    date = fields.Date('Date', states={'done': [('readonly', True)]}, default=fields.Date.context_today)
    # To remove after
    journal_id = fields.Many2one('account.journal', string='Journal', required=False,
                                 states={'done': [('readonly', True)]}, domain=[('type', 'in', ('bank', 'cash'))])

    note = fields.Text('Notes', states={'done': [('readonly', True)]})
    cheque_lines = fields.One2many('paiement.cheque.client', 'paiement_record_id', string=u'Chèques', readonly=True)
    effet_lines = fields.One2many('paiement.effet.client', 'paiement_record_id', string=u'Effets', readonly=True)
    ov_lines = fields.One2many('paiement.ov.client', 'paiement_record_id', string=u'OV', readonly=True)
    cb_lines = fields.One2many('paiement.cb.client', 'paiement_record_id', string=u'CB', readonly=True)
    cash_lines = fields.One2many('paiement.cash.client', 'paiement_record_id', string=u'Espèces', readonly=True)
    paiement_lines = fields.One2many('paiement.record.line', 'paiement_record_id', string=u'Lignes de Paiement', states={'done': [('readonly', True)]})
    amount = fields.Float(compute='_calc_amount', string=u'Montant des paiements', store=False)
    amount_invoices = fields.Float(compute='_calc_amount', string=u'Montant des factures', store=False)
    amount_avoirs = fields.Float(compute='_calc_amount', string=u'Montant des avoirs', store=False)
    amount_diff = fields.Float(compute='_calc_amount', string=u'Différence', store=False)
    caisse_id = fields.Many2one('paiement.caisse', default=_default_caisse, string='Caisse', required=True, states={'done':[('readonly', True)]})
    invoice_ids = fields.Many2many('account.move', 'paiement_record_invoice_rel', 'paiement_record_id','invoice_id', u'Factures', states={'done':[('readonly', True)]})
    state = fields.Selection([('draft', 'Brouillon'),
                              ('done', u'Validé'),
                              ('cancel', u'Annulé')],
                              default='draft', string='Etat', readonly=True, required=True, track_visibility='onchange')

    @api.constrains('invoice_ids')
    def _check_amount_diff(self):
        for rec in self:
            montant_invoice = 0.0
            depassement = False
            for invoice in rec.invoice_ids:
                if invoice.type == 'out_invoice':
                    if depassement == True:
                        raise UserError(u"Le montant des factures ne doit pas dépasser le montant des paiements")
                    montant_invoice+= invoice.amount_residual
                    if montant_invoice > self.amount + self.amount_avoirs:
                        depassement = True

    @api.model
    def get_model(self,type, company_id):
        res = False
        if type == 'cheque':
            model_id = self.env['paiement.cheque.model.client'].search([('company_id', '=', company_id)], limit=1)
            if model_id:
                res = model_id.id
        if type == 'effet':
            model_id = self.env['paiement.effet.model.client'].search([('company_id', '=', company_id)], limit=1)
            if model_id:
                res = model_id.id
        return res

    def get_invoices_number(self):
        invoices_number = ''
        for invoice in self.invoice_ids:
            invoices_number += invoice.name + '-'
        return invoices_number

    def create_acc_doc(self,record_line):
        effet_client_obj = self.env['paiement.effet.client']
        cheque_client_obj = self.env['paiement.cheque.client']
        ov_client_obj = self.env['paiement.ov.client']
        cash_client_obj = self.env['paiement.cash.client']
        cb_client_obj = self.env['paiement.cb.client']

        vals = {
            'name': record_line.paiement_ref,
            'amount': record_line.amount,
            'journal_id': record_line.journal_id.id,
            'date': record_line.paiement_record_id.date,
            'note': self.get_invoices_number(),
            'client': record_line.paiement_record_id.client_id.id,
            'caisse_id': record_line.paiement_record_id.caisse_id.id,
            'company_id': record_line.paiement_record_id.company_id.id,
            'analytic_account_id': record_line.analytic_account_id.id,
            'paiement_record_id': record_line.paiement_record_id.id
        }
        if record_line.type == 'cash':
            vals['name'] = self.env['ir.sequence'].next_by_code('paiement.cash.client')
            cash_id = cash_client_obj.create(vals)
            cash_id.action_caisse()
            return cash_id

        if record_line.type == 'effet':
            if not self.get_model('effet', vals['company_id']):
                raise UserError(u"Vous devez créer un modèle d'effet")
            vals['model_id'] = self.get_model('effet', vals['company_id'])
            vals['due_date'] = record_line.due_date
            effet_id = effet_client_obj.create(vals)
            effet_id.action_caisse()
            return effet_id

        if record_line.type == 'cheque':
            if not self.get_model('cheque', vals['company_id']):
                raise UserError(u"Vous devez créer un modèle chèque")
            vals['model_id'] = self.get_model('cheque', vals['company_id'])
            vals['due_date'] = record_line.due_date
            cheque_id = cheque_client_obj.create(vals)
            cheque_id.action_caisse()
            return cheque_id

        if record_line.type == 'ov':
            vals['due_date'] = record_line.due_date
            ov_id = ov_client_obj.create(vals)
            ov_id.action_caisse()
            return ov_id

        if record_line.type == 'cb':
            vals['due_date'] = record_line.due_date
            cb_id = cb_client_obj.create(vals)
            cb_id.action_caisse()
            return cb_id

    def action_done(self):
        for rec in self:
            for line in rec.paiement_lines:
                rec.create_acc_doc(line)
            rec.write({'state': 'done'})
            #Reconciliation
            #self.trans_rec_reconcile_full()

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_draft(self):
        for rec in self:
            rec.cheque_lines.unlink()
            rec.effet_lines.unlink()
            rec.ov_lines.unlink()
            rec.cash_lines.unlink()
            rec.cb_lines.unlink()
            rec.write({'state': 'draft'})

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(u"Vous ne pouvez pas supprimer un paiement dans l'état validé")
        return super(PaiementRecord, self).unlink()

    def trans_rec_reconcile_full(self):

        move_ids = []
        debit = 0.0
        credit = 0.0
        for rec in self:
            #Factures et avoirs
            for inv in rec.invoice_ids:
                for move_line in inv.move_id.line_ids:
                    if move_line.account_id.type == 'receivable':
                        move_ids.append(move_line.id)
                        debit += move_line.debit
                        credit += move_line.credit
                        print(credit,debit,"KHALID1")

            #Chèques
            for cheque in rec.cheque_lines:
                for move_line in cheque.move_line_ids:
                    if move_line.account_id.type == 'receivable':
                        move_ids.append(move_line.id)
                        debit += move_line.debit
                        credit += move_line.credit
            #Effets
            for effet in rec.effet_lines:
                for move_line in effet.move_line_ids:
                    if move_line.account_id.type == 'receivable':
                        move_ids.append(move_line.id)
                        debit += move_line.debit
                        credit += move_line.credit
            #OV
            for ov in rec.ov_lines:
                for move_line in ov.move_line_ids:
                    if move_line.account_id.type == 'receivable':
                        move_ids.append(move_line.id)
                        debit += move_line.debit
                        credit += move_line.credit
            # CB
            for cb in rec.ov_lines:
                for move_line in cb.move_line_ids:
                    if move_line.account_id.type == 'receivable':
                        move_ids.append(move_line.id)
                        debit += move_line.debit
                        credit += move_line.credit
            #Cash
            for cash in rec.cash_lines:
                for move_line in cash.move_line_ids:
                    if move_line.account_id.type == 'receivable':
                        move_ids.append(move_line.id)
                        debit += move_line.debit
                        credit += move_line.credit
        if debit == credit:
            move_lines = self.env['account.move.line'].browse(move_ids)
            move_lines.reconcile()
        if debit > credit:
            move_lines = self.env['account.move.line'].browse(move_ids)
            move_lines.reconcile_partial()


class PaiementRecordLine(models.Model):
    _name = "paiement.record.line"
    _description = "Ligne Paiement Client"

    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    paiement_record_id = fields.Many2one('paiement.record', 'Paiement')
    type = fields.Selection([
                    ('cash', u'Espèce'),
                    ('effet', u'Effet'),
                    ('cheque', u'Chèque'),
                    ('ov', 'OV'),
                    ('cb', 'CB')], u'Méthode de Paiement', required=True)
    amount = fields.Float('Montant', help='Montant', required=True)
    paiement_ref = fields.Char(u'Référence de Paiement')
    due_date = fields.Date(u"Echéance")
    client_bank_id = fields.Many2one("res.partner.bank", "Banque client")
    analytic_account_id = fields.Many2one('account.analytic.account', 'Compte Analytique')
