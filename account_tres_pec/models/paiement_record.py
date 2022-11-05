# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class TresFees(models.Model):
    _inherit = 'tres.fees'

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

            if record.pec_client_id:
                journal_id = record.pec_client_id.journal_id
                date = record.pec_client_id.date
                name = record.pec_client_id.name
                ref = record.pec_client_id.note
                partner_id = record.pec_client_id.client.id

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

    pec_client_id = fields.Many2one('paiement.pec.client', string=u'Prise en charge client')


class PaiementCaisse(models.Model):
    _inherit = 'paiement.caisse'

    @api.depends('cheque_lines', 'effet_lines', 'ov_lines', 'pec_lines', 'cash_lines.amount')
    def _calc_total_amount(self):
        for rec in self:
            rec.nb_cheques = len(rec.cheque_lines)
            rec.nb_effets = len(rec.effet_lines)
            rec.nb_ov = len(rec.ov_lines)
            rec.nb_cb = len(rec.cb_lines)
            rec.nb_pec = len(rec.pec_lines)
            rec.total_amount = sum(cheque.amount for cheque in rec.cheque_lines) + sum(effet.amount for effet in rec.effet_lines)+ \
                                sum(ov.amount for ov in rec.ov_lines) + sum(cash.amount for cash in rec.cash_lines) + sum(cb.amount for cb in rec.cb_lines) \
                                + sum(cb.amount for cb in rec.pec_lines)

    pec_lines = fields.One2many('paiement.pec.client', 'caisse_id', string=u'Prises en charge', readonly=True)
    nb_pec = fields.Float(compute='_calc_total_amount', string=u"Nombre de PES")


class PaiementRecord(models.Model):
    _inherit = "paiement.record"

    pec_lines = fields.One2many('paiement.pec.client', 'paiement_record_id', string=u'PEC', readonly=True)

    @api.model
    def get_model(self, type, company_id):
        res = False
        if type == 'cheque':
            model_id = self.env['paiement.cheque.model.client'].search([('company_id', '=', company_id)], limit=1)
            if model_id:
                res = model_id.id
        if type == 'effet':
            model_id = self.env['paiement.effet.model.client'].search([('company_id', '=', company_id)], limit=1)
            if model_id:
                res = model_id.id

        if type == 'pec':
            model_id = self.env['paiement.pec.model.client'].search([('company_id', '=', company_id)], limit=1)
            if model_id:
                res = model_id.id
        return res

    def create_acc_doc(self,record_line):
        effet_client_obj = self.env['paiement.effet.client']
        cheque_client_obj = self.env['paiement.cheque.client']
        ov_client_obj = self.env['paiement.ov.client']
        cash_client_obj = self.env['paiement.cash.client']
        cb_client_obj = self.env['paiement.cb.client']
        pec_client_obj = self.env['paiement.pec.client']

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

        if record_line.type == 'pec':
            vals['due_date'] = record_line.due_date
            vals['model_id'] = self.get_model('pec', vals['company_id'])
            pec_id = pec_client_obj.create(vals)
            pec_id.action_caisse()
            return pec_id

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
            rec.pec_lines.unlink()
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
    _inherit = "paiement.record.line"
    _description = "Ligne Paiement Client"

    type = fields.Selection(selection_add=[
        ('pec', 'PEC')
    ], ondelete={'pec': 'cascade'})