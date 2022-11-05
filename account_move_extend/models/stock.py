# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'stock.move'

    invoiced_qty = fields.Float('Quantité facturé', compute='compute_invoiced_qty')

    def compute_invoiced_qty(self):
        for rec in self:
            move_ids = self.env['account.move'].search([('picking_id', '=', rec.picking_id.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted')])
            print('move_ids', move_ids)
            rec.invoiced_qty = 0.0
            for move in move_ids:
                qty_product_done = sum(move.invoice_line_ids.
                                       filtered(lambda line: line.product_id == rec.product_id).mapped('quantity'))
                rec.invoiced_qty = qty_product_done