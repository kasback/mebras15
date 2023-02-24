# -*- encoding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from collections import defaultdict


class ResPartner(models.Model):
    _inherit = 'res.partner'

    dso_target = fields.Float(string='DSO Target (Nbr de jours)')
    nbr_jrs = fields.Float('Nbr de jours en arrière')
    marge = fields.Monetary('Marge', compute='compute_marge', store=True)
    authorized_exceeding = fields.Monetary('Dépassement autorisé', compute='compute_marge', store=True)
    variation = fields.Monetary('Variation', compute='compute_marge', store=True)
    partner_dso = fields.Float(string='DSO')
    num_of_days = fields.Float(string='Nbr de jours')
    target_amount = fields.Float(string='Montant Target')
    recovery_amount = fields.Float(string='Recouvrement')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(ResPartner, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                                 lazy=lazy)
        computed_fields = ['total_overdue', 'target_amount', 'recovery_amount', 'marge',
                           'authorized_exceeding', 'variation']
        for computed_field in computed_fields:
            if computed_field in fields:
                for line in res:
                    if '__domain' in line:
                        lines = self.search(line['__domain'])
                        total_total_overdue = 0.0
                        total_target_amount = 0.0
                        total_recovery_amount = 0.0
                        total_marge = 0.0
                        total_authorized_exceeding = 0.0
                        total_variation = 0.0
                        for record in lines:
                            total_total_overdue += record.total_overdue
                            total_target_amount += record.target_amount
                            total_recovery_amount += record.recovery_amount
                            total_marge += record.marge
                            total_authorized_exceeding += record.authorized_exceeding
                            total_variation += record.variation
                        line['total_overdue'] = total_total_overdue
                        line['target_amount'] = total_target_amount
                        line['recovery_amount'] = total_recovery_amount
                        line['marge'] = total_marge
                        line['authorized_exceeding'] = total_authorized_exceeding
                        line['variation'] = total_variation
        return res

    def get_marge(self, invoice_lines):
        marge = 0
        for line in invoice_lines:
            lot_ids = line.mapped('prod_lot_ids')
            if not lot_ids:
                continue
            for lot in lot_ids:
                move_line_ids = line.mapped('sale_line_ids.move_ids.move_line_ids').\
                    filtered(lambda l: l.lot_id == lot)
                for ml in move_line_ids:
                    qty_done = 0
                    if ml.picking_code == "incoming":
                        qty_done = -ml.qty_done
                    elif ml.picking_code == "outgoing":
                        qty_done = ml.qty_done
                    operation = (qty_done * round(lot.lot_price_list, 2)) - \
                                (round(lot.lot_cost, 2) * qty_done)
                    marge += operation
        return marge

    @api.depends('nbr_jrs')
    def compute_marge(self):
        AccountMoveLine = self.env['account.move.line']
        domain = [('quantity', '>', '0'), ('move_id.move_type', '=', 'out_invoice'), ('move_id.state', '=', 'posted')]
        for rec in self:
            domain += [('move_id.partner_id', '=', rec.id)]
            invoice_lines = AccountMoveLine.search(domain)
            rec.marge = self.get_marge(invoice_lines)
            rec.authorized_exceeding = 0.0
            if rec.nbr_jrs:
                new_date = fields.Date.today() - relativedelta(days=rec.nbr_jrs)
                domain += [('move_id.invoice_date', '>=', new_date)]
                invoice_lines = AccountMoveLine.search(domain)
                rec.authorized_exceeding = self.get_marge(invoice_lines)
            rec.variation = rec.authorized_exceeding - rec.total_overdue

    def compute_all_marges(self):
        AccountMoveLine = self.env['account.move.line']
        partner_ids = self.env['res.partner'].search([])
        for rec in partner_ids:
            domain = [('move_id.move_type', '=', 'out_invoice'),
                      ('move_id.state', '=', 'posted'), ('move_id.partner_id', '=', rec.id), ('quantity', '>', '0')]
            invoice_lines = AccountMoveLine.search(domain)
            rec.marge = self.get_marge(invoice_lines)
            rec.authorized_exceeding = 0.0
            if rec.nbr_jrs:
                new_date = fields.Date.today() - relativedelta(days=rec.nbr_jrs)
                domain += [('move_id.invoice_date', '>=', new_date)]
                invoice_lines = AccountMoveLine.search(domain)
                rec.authorized_exceeding = self.get_marge(invoice_lines)
            rec.variation = rec.authorized_exceeding - rec.total_overdue