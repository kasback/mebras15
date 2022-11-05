# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    taxe_cost_line_ids = fields.One2many('tax.landed.cost.line', 'landed_cost_id', 'Lignes de TVA')
    total_tax_landed_cost = fields.Monetary('Total TVA des coûts logistiques', currency_field='currency_id', compute='_compute_tax_landed_cost', default=0.0)

    @api.depends('taxe_cost_line_ids')
    def _compute_tax_landed_cost(self):
        for rec in self:
            rec.total_tax_landed_cost = sum(rec.taxe_cost_line_ids.mapped('amount'))


class TaxLandedCostLine(models.Model):
    _name = 'tax.landed.cost.line'

    landed_cost_id = fields.Many2one('stock.landed.cost', 'Fiche Côut Logistique')
    amount = fields.Float('Montant', default=0.0)
    product_id = fields.Many2one('product.product', 'Product', required=True)
