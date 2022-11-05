# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class TresFees(models.Model):
    _inherit = 'tres.fees'

    bordereau_id = fields.Many2one('paiement.bordereau', 'Bordereau')


class PaiementEffetClient(models.Model):
    _inherit = "paiement.effet.client"

    bordereau_id = fields.Many2one('paiement.bordereau', 'Bordereau')


class PaiementChequeClient(models.Model):
    _inherit = "paiement.cheque.client"

    bordereau_id = fields.Many2one('paiement.bordereau', 'Bordereau')


class PaiementBordereau(models.Model):
    _name = 'paiement.bordereau'
    _description = 'Bordereau'

    @api.depends('cheque_lines', 'effet_lines')
    def _calc_total_amount(self):
        self.total_amount_ok = sum(cheque.amount for cheque in self.cheque_lines if cheque.state == 'payed') + sum(
            effet.amount for effet in self.effet_lines if effet.state == 'payed')
        self.total_amount_ko = sum(
            cheque.amount for cheque in self.cheque_lines if cheque.state not in ['payed', 'rejected']) + sum(
            effet.amount for effet in self.effet_lines if effet.state not in ['payed', 'rejected'])
        self.total_amount_rejet = sum(
            cheque.amount for cheque in self.cheque_lines if cheque.state == 'rejected') + sum(
            effet.amount for effet in self.effet_lines if effet.state == 'rejected')
        self.nb_cheques = len(self.cheque_lines)
        self.nb_effets = len(self.effet_lines)
        self.total_amount = sum(self.cheque_lines.mapped('amount'))+ sum(self.effet_lines.mapped('amount'))

    name = fields.Char(string=u'Numéro', required=True)
    company_id = fields.Many2one('res.company', readonly=True, string=u'Societé',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.bordereau'))
    cheque_lines = fields.One2many('paiement.cheque.client', 'bordereau_id', string=u'Chèques', copy=False)
    effet_lines = fields.One2many('paiement.effet.client', 'bordereau_id', string=u'Effets', copy=False)
    date = fields.Date(string=u'Date', required=True)
    courssier_id = fields.Many2one('res.users', string=u'Coursier')
    journal_id = fields.Many2one('account.journal', string=u'Journal Banque', required=True,
                                 domain=[('type', '=', 'bank')])
    total_amount = fields.Float(compute='_calc_total_amount', string=u'Montant total')
    total_amount_ok = fields.Float(compute='_calc_total_amount', string=u'Montant total encaissé')
    total_amount_ko = fields.Float(compute='_calc_total_amount', string=u'Montant total non encaissé')
    total_amount_rejet = fields.Float(compute='_calc_total_amount', string=u'Montant total rejet')
    nb_cheques = fields.Integer(compute='_calc_total_amount', string=u'Nombre de chèques')
    nb_effets = fields.Integer(compute='_calc_total_amount', string=u"Nombre d'effets")
    type = fields.Selection([('effet', 'Effet'), ('cheque', u'Chèque')], 'Type', readonly=True)
    tres_fees_ids = fields.One2many('tres.fees', 'bordereau_id', string=u'Frais bancaires', copy=False)
    date_encaissement = fields.Date(string=u'Date encaissement')
    state = fields.Selection([('draft', 'Brouillon'), ('done', u'Validé'), ('received', u'Déposé à la banque')],
                             string='Etat', default='draft', readonly=True, required=True)

    def valider_bordereau(self):
        for record in self:
            for ch in record.cheque_lines:
                if ch.state == 'caisse':
                    ch.action_caisse_centrale()
                    ch.action_received()
                if ch.state == 'caisse_centrale':
                    ch.action_received()
                ch.write({'caisse_id': False, 'journal_id': ch.journal_id.id})
            for ef in record.effet_lines:
                if ef.state == 'caisse':
                    ef.action_caisse_centrale()
                    ef.action_received()
                if ef.state == 'caisse_centrale':
                    ef.action_received()
                ef.action_received()
                # ef.write({'caisse_id': False, 'journal_id': record.journal_id.id})
                ef.write({'caisse_id': False, 'journal_id': ef.journal_id.id})
            record.write({'state': 'done'})
        return True

    def rec_bordereau(self):
        attach_obj = self.env['ir.attachment']
        for record in self:
            has_attachment = self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.has_attachment')
            if has_attachment:
                attachment_ids = attach_obj.search(
                    [('res_model', '=', 'paiement.bordereau'), ('res_id', '=', record.id)])
                if not attachment_ids:
                    raise UserError(u'Vous devez attacher le bordereau scanné')
            for ch in record.cheque_lines:
                if ch.state == 'received':
                    ch.action_at_bank()
            for ef in record.effet_lines:
                if ef.state == 'received':
                    ef.action_at_bank()
            record.write({'state': 'received'})
        return True

    def action_post_fees(self):
        for record in self:
            for fees in record.tres_fees_ids:
                if fees.state == 'draft':
                    fees.create_account_lines()

    def back_to_draft(self):
        for record in self:
            move_ids = []
            for l in record.effet_lines:
                for mv in l.move_line_ids:
                    mv.move_id.button_cancel()
                    move_ids.append(mv.move_id.id)
                l.move_line_ids.unlink()
                l.write({'state': 'draft'})
                l.action_caisse()
            for l in record.cheque_lines:
                for mv in l.move_line_ids:
                    mv.move_id.button_cancel()
                    move_ids.append(mv.move_id.id)
                l.move_line_ids.unlink()
                l.write({'state': 'draft'})
                l.action_caisse()
            print('mmmm', move_ids)
            self.env['account.move'].browse(move_ids).unlink()
            record.write({'state': 'draft'})
        return True

    # @api.model
    # def default_get(self, fields):
    #     res = super(PaiementBordereau, self).default_get(fields)
    #     res['name'] = '/'
    #     return res
    #
    # @api.model
    # def create(self, vals):
    #     if vals['name'] == '/' or not vals['name']:
    #         vals['name'] = self.env['ir.sequence'].next_by_code('paiement.bordereau')
    #     return super(PaiementBordereau, self).create(vals)
    #
    # def copy(self, default=None):
    #     if not default:
    #         default = {}
    #     default.update({
    #         'state': 'draft',
    #         'name':  self.env['ir.sequence'].next_by_code('paiement.bordereau')
    #     })
    #     return super(PaiementBordereau, self).copy(default)
