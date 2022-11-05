# -*- coding: utf-8 -*-

from odoo import models,fields, api
from . import convertion


class AccountInvoice(models.Model):
    _inherit='account.move'

    total_a_payer = fields.Float('Total à payer', compute='compute_droit_timbre')
    comment = fields.Text(readonly=False)
    amount_text = fields.Char(compute='_get_amount_text', string='Montant en lettre', store=True, )

    @api.depends('amount_total', 'total_a_payer', 'currency_id.symbol')
    def _get_amount_text(self):
        for invoice in self:
            invoice.amount_text = convertion.trad(invoice.amount_total,invoice.currency_id.name)
