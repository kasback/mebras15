# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ChequeToChange(models.TransientModel):
    _name = "cheque_to_change"

    def action_to_change(self):
        active_ids = self.env.context['active_ids']
        paiement_cheque_client_obj = self.env["paiement.cheque.client"]
        for rec in self:
            rec.cheque_id.write({'cheque_origin_id':active_ids[0]})
        for cheque in paiement_cheque_client_obj.browse(active_ids):
            cheque.write({'state': 'to_change',
                          'name': cheque.name+'/'+'Rejete',
                          'rejete': True})
        for rec in self:
            # if rec.effet_id:
            #     effet = rec.effet_id
            # elif rec.cash_id:
            #     cash = rec.cash_id
            # elif rec.ov_id:
            #     ov = rec.ov_id
            for cheque in paiement_cheque_client_obj.browse(active_ids):
                if rec.effet_id:
                    rec.effet_id.origin = cheque.name
                elif rec.cash_id:
                    rec.cash_id.origin = cheque.name
                elif rec.ov_id:
                    rec.ov_id.origin = cheque.name
        return True

    cheque_id = fields.Many2one('paiement.cheque.client', string=u'Chèque')
    cash_id = fields.Many2one('paiement.cash.client', string=u'Espèce')
    effet_id = fields.Many2one('paiement.effet.client', string=u'Effet')
    ov_id = fields.Many2one('paiement.ov.client', string=u'OV')
    type = fields.Selection([
        ('cash', u'Espèce'),
        ('effet', u'Effet'),
        ('cheque', u'Chèque'),
        ('ov', 'OV'), ], u'Méthode de Paiement', select=True, required=True)


class EffetToChange(models.TransientModel):
    _name = "effet_to_change"

    def action_to_change(self):
        active_ids=self.env.context['active_ids']
        paiement_effet_client_obj = self.env["paiement.effet.client"]
        for rec in self:
            rec.effet_id.write({'effet_origin_id': active_ids[0]})
        for effet in paiement_effet_client_obj.browse(active_ids):
            effet.write({'state': 'to_change',
                         'name': effet.name+'/'+'Rejete',
                         'rejete': True})
        for rec in self:
            for effet in paiement_effet_client_obj.browse(active_ids):
                    if rec.cheque_id:
                        rec.cheque_id.origin = effet.name
                    elif rec.cash_id:
                        rec.cash_id.origin = effet.name
                    elif rec.ov_id:
                        rec.ov_id.origin = effet.name
        return True

    effet_id = fields.Many2one('paiement.effet.client', strinG=u'Effet')
    cash_id = fields.Many2one('paiement.cash.client', string=u'Espèce')
    cheque_id = fields.Many2one('paiement.cheque.client', string=u'Cheque')
    ov_id = fields.Many2one('paiement.ov.client', string=u'OV')
    type = fields.Selection([
        ('cash', u'Espèce'),
        ('effet', u'Effet'),
        ('cheque', u'Chèque'),
        ('ov', 'OV'), ], u'Méthode de Paiement', select=True, required=True)
