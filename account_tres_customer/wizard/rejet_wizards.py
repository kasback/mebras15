# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RejetChequeWizard(models.TransientModel):
    _name = "rejet.cheque.wizard"

    in_relevet = fields.Boolean(u'Apparaît dans le relevé bancaire')
    date_rejet = fields.Date(u'Date de rejet', required=True)

    def reject_action(self):
        cheque = self.env[self._context.get('active_model')].search([('id', '=', self._context.get('active_id'))])
        cheque.open_reject_wizard(self.in_relevet, self.date_rejet)


class RejetEffetWizard(models.TransientModel):
    _name = "rejet.effet.wizard"

    in_relevet = fields.Boolean(u'Apparaît dans le relevé bancaire')
    date_rejet = fields.Date(u'Date de rejet', required=True)

    def reject_action(self):
        cheque = self.env[self._context.get('active_model')].search([('id', '=', self._context.get('active_id'))])
        cheque.open_reject_wizard(self.in_relevet, self.date_rejet)

