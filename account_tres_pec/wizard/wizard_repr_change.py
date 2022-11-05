# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ChequeToChange(models.TransientModel):
    _inherit = "cheque_to_change"

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
                elif rec.pec_id:
                    rec.pec_id.origin = cheque.name
        return True

    pec_id = fields.Many2one('paiement.pec.client', string=u'PEC')
    type = fields.Selection(selection_add=[
        ('pec', 'PEC')
    ], ondelete={'pec': 'cascade'})


class EffetToChange(models.TransientModel):
    _inherit = "effet_to_change"

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
                    elif rec.pec_id:
                        rec.pec_id.origin = effet.name
        return True

    pec_id = fields.Many2one('paiement.pec.client', string=u'PEC')
    type = fields.Selection(selection_add=[
        ('pec', 'PEC')
    ], ondelete={'pec': 'cascade'})
