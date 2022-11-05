# -*- encoding: utf-8 -*-

from odoo import models,fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    pec_client_id = fields.Many2one('paiement.pec.client', 'Prise en charge client')
