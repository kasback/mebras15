# -*- encoding: utf-8 -*-
from statistics import mean

from odoo import models, fields, api


class BudgetSale(models.Model):
    _name = 'budget.budget'
    _rec_name = 'product_id'

    partner_id = fields.Many2one('res.partner', 'Partenaire')
    product_id = fields.Many2one('product.product', 'Article')
    lot_id = fields.Many2one('stock.production.lot', 'Numéro de lot / série')
    qty = fields.Float('Quantités')
    lot_cost = fields.Float(string='Coût')
    unit_amount = fields.Float(string='Prix Unitaire')
    amount_total = fields.Float(string='Total')
    marge = fields.Float(string='Marge')
    date = fields.Date(string='Date')
    type = fields.Selection([('prev', 'Prévisionnel'), ('real', 'Réel')], default='prev', string='Prévisionnel/Réel')
    user_type = fields.Selection([('com', 'Commercial'), ('dir', 'Direction')], default='com',
                                 string='Entité d\'estimation')
    budget_type = fields.Selection([('sale', 'Ventes'), ('purchase', 'Achats')], default='sale',
                                 string='Type de budget')
    estimation_budget_id = fields.Many2one('budget.budget', 'Prévisions Estimatives')
    estimation_budget_dir_id = fields.Many2one('budget.budget', 'Prévisions Estimatives Direction')

    # Prévisionnel Commercial
    qty_prev = fields.Float(string='Quantités P.', related='estimation_budget_id.qty')
    lot_cost_prev = fields.Float(string='Coût P.', related='estimation_budget_id.lot_cost')
    unit_amount_prev = fields.Float(string='PU P.', related='estimation_budget_id.unit_amount')
    amount_total_prev = fields.Float(string='Total P.', related='estimation_budget_id.amount_total')
    marge_prev = fields.Float(string='Marge P.', related='estimation_budget_id.marge')
    diff_num_qty = fields.Float('Écart Quantités', compute='compute_diff_quantities')
    diff_num_lot_cost = fields.Float(string='Écart Coût', compute='compute_diff_quantities')
    diff_num_unit_amount = fields.Float(string='Écart PV', compute='compute_diff_quantities')
    diff_num_amount_total = fields.Float(string='Écart Montant', compute='compute_diff_quantities')
    diff_num_marge = fields.Float(string='Écart Marge', compute='compute_diff_quantities')

    # Prévisionnel Direction
    qty_prev_dir = fields.Float(string='Quantités P.', related='estimation_budget_dir_id.qty')
    lot_cost_prev_dir = fields.Float(string='Coût P.', related='estimation_budget_dir_id.lot_cost')
    unit_amount_prev_dir = fields.Float(string='PU P.', related='estimation_budget_dir_id.unit_amount')
    amount_total_prev_dir = fields.Float(string='Total P.', related='estimation_budget_dir_id.amount_total')
    marge_prev_dir = fields.Float(string='Marge P.', related='estimation_budget_dir_id.marge')
    diff_num_qty_dir = fields.Float('Écart Quantités', compute='compute_diff_quantities')
    diff_num_lot_cost_dir = fields.Float(string='Écart Coût', compute='compute_diff_quantities')
    diff_num_unit_amount_dir = fields.Float(string='Écart PV', compute='compute_diff_quantities')
    diff_num_amount_total_dir = fields.Float(string='Écart Montant', compute='compute_diff_quantities')
    diff_num_marge_dir = fields.Float(string='Écart Marge', compute='compute_diff_quantities')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(BudgetSale, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                         orderby=orderby,
                                                         lazy=lazy)
        target_fields = ['unit_amount', 'lot_cost']
        for tg in target_fields:
            if tg in fields:
                for line in res:
                    if '__domain' in line:
                        lines = self.search(line['__domain'])
                        line['unit_amount'] = mean(lines.mapped('unit_amount'))
                        line['lot_cost'] = mean(lines.mapped('lot_cost'))
        return res

    def compute_diff_quantities(self):
        for rec in self:
            rec.diff_num_marge = 0
            rec.diff_num_qty = 0
            rec.diff_num_lot_cost = 0
            rec.diff_num_unit_amount = 0
            rec.diff_num_amount_total = 0
            rec.diff_num_marge_dir = 0
            rec.diff_num_qty_dir = 0
            rec.diff_num_lot_cost_dir = 0
            rec.diff_num_unit_amount_dir = 0
            rec.diff_num_amount_total_dir = 0
            if rec.estimation_budget_id:
                estimated_marge = (rec.unit_amount - rec.lot_id.lot_cost) * rec.estimation_budget_id.qty
                rec.diff_num_marge = rec.marge - estimated_marge
                rec.diff_num_qty = rec.qty - rec.estimation_budget_id.qty
                rec.diff_num_lot_cost = rec.lot_cost - rec.estimation_budget_id.lot_cost
                rec.diff_num_unit_amount = rec.unit_amount - rec.estimation_budget_id.unit_amount
                rec.diff_num_amount_total = rec.amount_total - \
                                            (rec.estimation_budget_id.unit_amount * rec.estimation_budget_id.qty)
                rec.diff_num_marge = rec.marge - estimated_marge
            if rec.estimation_budget_dir_id:
                estimated_marge = (rec.unit_amount - rec.lot_id.lot_cost) * rec.estimation_budget_dir_id.qty
                rec.diff_num_marge = rec.marge - estimated_marge
                rec.diff_num_qty = rec.qty - rec.estimation_budget_dir_id.qty
                rec.diff_num_lot_cost = rec.lot_cost - rec.estimation_budget_dir_id.lot_cost
                rec.diff_num_unit_amount = rec.unit_amount - rec.estimation_budget_dir_id.unit_amount
                rec.diff_num_amount_total = rec.amount_total - \
                                            (rec.estimation_budget_dir_id.unit_amount * rec.estimation_budget_dir_id.qty)
                rec.diff_num_marge = rec.marge - estimated_marge

    def compute_sale_lines(self):
        Budget = self.env['budget.budget']
        Budget.unlink()
        lot_ids = self.env['stock.production.lot'].search([])
        for lot in lot_ids:
            invoice_line_ids = self.env['account.move.line'].search([('prod_lot_ids', 'in', lot.id),
                                                                     ('move_id.move_type', '=', 'out_invoice')])
            for il in invoice_line_ids:
                qty_invoiced = il.quantity
                price_unit = il.price_unit
                amount_total = price_unit * qty_invoiced
                invoice_id = il.move_id
                marge = (price_unit - lot.lot_cost) * qty_invoiced
                Budget.create({
                    'partner_id': invoice_id.partner_id.id,
                    'product_id': lot.product_id.id,
                    'lot_id': lot.id,
                    'qty': qty_invoiced,
                    'lot_cost': lot.lot_cost,
                    'unit_amount': price_unit,
                    'amount_total': amount_total,
                    'marge': marge,
                    'date': invoice_id.invoice_date,
                    'type': 'real',
                    'budget_type': 'sale'
                })

    def compute_purchase_lines(self):
        Budget = self.env['budget.budget']
        Budget.unlink()
        lot_ids = self.env['stock.production.lot'].search([])
        for lot in lot_ids:
            move_line_ids = self.env['stock.move.line'].search([('lot_id', '=', lot.id),
                                                                   ('move_id.purchase_line_id', '!=', False),
                                                                   ('picking_code', '=', 'incoming')])
            for ml in move_line_ids:
                qty = ml.qty_done
                price_unit = ml.move_id.purchase_line_id.real_purchase_price
                amount_total = price_unit * qty
                purchase_id = ml.move_id.purchase_line_id.order_id
                Budget.create({
                    'partner_id': purchase_id.partner_id.id,
                    'product_id': lot.product_id.id,
                    'lot_id': lot.id,
                    'qty': qty,
                    'lot_cost': lot.lot_cost,
                    'unit_amount': price_unit,
                    'amount_total': amount_total,
                    'date': ml.move_id.picking_id.date_done,
                    'type': 'real',
                    'budget_type': 'purchase'
                })
