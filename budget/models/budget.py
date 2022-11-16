# -*- encoding: utf-8 -*-
from statistics import mean

from odoo import models, fields, api


class BudgetTag(models.Model):
    _name = 'budget.tag'

    name = fields.Char('Nom')


class BudgetSale(models.Model):
    _name = 'budget.budget'
    _rec_name = 'product_id'

    partner_id = fields.Many2one('res.partner', 'Partenaire')
    product_id = fields.Many2one('product.product', 'Article')
    lot_ids = fields.Many2many('stock.production.lot', string='Lots')
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
    account_move_line_id = fields.Many2one('account.move.line', 'Mouvement source facture')
    move_line_ids = fields.Many2many('stock.move.line', string='Mouvement de stock')
    tag_ids = fields.Many2many('budget.tag', string="Étiquettes")
    company_id = fields.Many2one('res.company')
    # Prévisionnel
    qty_prev = fields.Float(string='Quantités P.')
    lot_cost_prev = fields.Float(string='Coût P.')
    unit_amount_prev = fields.Float(string='PU P.')
    amount_total_prev = fields.Float(string='Total P.', compute='compute_prev_qty')
    marge_prev = fields.Float(string='Marge P.', compute='compute_prev_qty')
    diff_num_qty = fields.Float('Écart Quantités')
    diff_num_lot_cost = fields.Float(string='Écart Coût')
    diff_num_unit_amount = fields.Float(string='Écart PV')
    diff_num_amount_total = fields.Float(string='Écart Montant')
    diff_num_marge = fields.Float(string='Écart Marge')

    def compute_prev_qty(self):
        for rec in self:
            rec.amount_total_prev = rec.qty_prev * rec.unit_amount_prev
            rec.marge_prev = rec.qty_prev * (rec.unit_amount_prev - rec.lot_cost_prev)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(BudgetSale, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                 orderby=orderby,
                                                 lazy=lazy)
        target_fields = ['unit_amount', 'lot_cost', 'diff_num_qty',
                         'diff_num_lot_cost',
                         'diff_num_unit_amount',
                         'diff_num_amount_total',
                         'diff_num_marge',
                         'amount_total_prev',
                         'marge_prev'
                         ]
        for tg in target_fields:
            if tg in fields:
                for line in res:
                    if '__domain' in line:
                        lines = self.search(line['__domain'])
                        real_marge = sum(lines.mapped('marge'))
                        real_qty = sum(lines.mapped('qty'))
                        real_lot_cost = mean(lines.mapped('lot_cost'))
                        real_unit_amount = mean(lines.mapped('unit_amount'))
                        real_amount_total = sum(lines.mapped('amount_total'))
                        estimated_marge = sum(lines.mapped('marge_prev'))
                        estimated_qty = sum(lines.mapped('qty_prev'))
                        estimated_lot_cost = sum(lines.mapped('lot_cost_prev'))
                        estimated_unit_amount = sum(lines.mapped('unit_amount_prev'))
                        estimated_amount_total = sum(lines.mapped('amount_total_prev'))
                        line['amount_total_prev'] = estimated_amount_total
                        line['marge_prev'] = estimated_marge
                        line['diff_num_marge'] = real_marge - estimated_marge
                        line['diff_num_qty'] = real_qty - estimated_qty
                        line['diff_num_lot_cost'] = real_lot_cost - estimated_lot_cost
                        line['diff_num_unit_amount'] = real_unit_amount - estimated_unit_amount
                        line['diff_num_amount_total'] = real_amount_total - estimated_amount_total
                        line['diff_num_marge'] = real_marge - estimated_marge
                        line['unit_amount'] = mean(lines.mapped('unit_amount'))
                        line['lot_cost'] = mean(lines.mapped('lot_cost'))
        return res

    def compute_sale_lines(self):
        Budget = self.env['budget.budget'].search([('type', '=', 'real'), ('budget_type', '=', 'sale')])
        Budget.unlink()
        product_ids = self.env['product.product'].search([])
        for product in product_ids:
            invoice_line_ids = self.env['account.move.line'].search([('product_id', '=', product.id),
                                                                     ('move_id.move_type', '=', 'out_invoice')])
            for il in invoice_line_ids:
                move_line_ids = il.mapped('sale_line_ids').mapped('move_ids'). \
                    mapped('move_line_ids').filtered(lambda ml: ml.picking_code == 'outgoing')
                lot_ids = move_line_ids.mapped('lot_id')
                lot_cost = mean(lot_ids.mapped('lot_cost')) if lot_ids.mapped('lot_cost') else 0
                qty_invoiced = il.quantity
                price_unit = il.price_unit
                amount_total = price_unit * qty_invoiced
                invoice_id = il.move_id
                marge = (price_unit - product.lot_cost) * qty_invoiced
                vals = {'partner_id': invoice_id.partner_id.id,
                        'product_id': product.id,
                        'qty': qty_invoiced,
                        'lot_cost': lot_cost,
                        'lot_ids': lot_ids.ids,
                        'unit_amount': price_unit,
                        'amount_total': amount_total,
                        'marge': marge,
                        'date': invoice_id.invoice_date,
                        'account_move_line_id': il.id,
                        'move_line_ids': move_line_ids.ids,
                        'type': 'real',
                        'budget_type': 'sale',
                        'user_type': 'com',
                        'company_id': il.company_id.id}
                Budget.create(vals)
                vals['user_type'] = 'dir'
                Budget.create(vals)

    def compute_purchase_lines(self):
        Budget = self.env['budget.budget'].search([('type', '=', 'real'), ('budget_type', '=', 'purchase')])
        Budget.unlink()
        product_ids = self.env['product.product'].search([])
        for product in product_ids:
            move_line_ids = self.env['stock.move.line'].search([('product_id', '=', product.id),
                                                                ('move_id.purchase_line_id', '!=', False),
                                                                ('picking_code', '=', 'incoming')])
            for ml in move_line_ids:
                lot_cost = ml.lot_id.lot_cost
                qty = ml.qty_done
                price_unit = ml.move_id.purchase_line_id.real_purchase_price
                amount_total = price_unit * qty
                purchase_id = ml.move_id.purchase_line_id.order_id
                vals = {'partner_id': purchase_id.partner_id.id,
                        'product_id': product.id,
                        'lot_ids': ml.lot_id.ids,
                        'qty': qty,
                        'lot_cost': lot_cost,
                        'unit_amount': price_unit,
                        'amount_total': amount_total,
                        'date': ml.move_id.picking_id.date_done,
                        'move_line_ids': ml.ids,
                        'type': 'real',
                        'budget_type': 'purchase',
                        'user_type': 'com',
                        'company_id': ml.company_id.id}
                Budget.create(vals)
                vals['user_type'] = 'dir'
                Budget.create(vals)
