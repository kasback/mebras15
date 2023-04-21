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
    purchase_value = fields.Float('Prix d\'achat', compute='_compute_purchase_value')
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
    cost_total_prev = fields.Float(string='P.A', compute='compute_prev_qty')
    amount_total_prev = fields.Float(string='Total P.', compute='compute_prev_qty')
    marge_prev = fields.Float(string='Marge P.', compute='compute_prev_qty')
    diff_num_qty = fields.Float('Écart Quantités')
    diff_num_lot_cost = fields.Float(string='Écart Coût')
    diff_num_unit_amount = fields.Float(string='Écart PV')
    diff_num_amount_total = fields.Float(string='Écart Montant')
    diff_num_marge = fields.Float(string='Écart Marge')

    def _compute_purchase_value(self):
        for rec in self:
            rec.purchase_value = rec.lot_cost * rec.qty

    def compute_prev_qty(self):
        for rec in self:
            rec.amount_total_prev = rec.qty_prev * rec.unit_amount_prev
            rec.cost_total_prev = rec.qty_prev * rec.lot_cost_prev
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
                         'marge_prev',
                         'purchase_value',
                         'cost_total_prev'
                         ]
        for tg in target_fields:
            if tg in fields:
                for line in res:
                    if '__domain' in line:
                        lines = self.search(line['__domain'])
                        real_qty = sum(lines.mapped('qty'))
                        cost_total_prev = sum(lines.mapped('cost_total_prev'))
                        real_amount_total = sum(lines.mapped('amount_total'))
                        real_purchase_value = sum(lines.mapped('purchase_value'))
                        marge = real_amount_total - real_purchase_value
                        real_lot_cost = real_purchase_value / real_qty if real_qty else 0
                        real_unit_amount = real_amount_total / real_qty if real_qty else 0
                        estimated_marge = sum(lines.mapped('marge_prev'))
                        estimated_qty = sum(lines.mapped('qty_prev'))
                        est_marge = estimated_marge / estimated_qty if estimated_qty else 0
                        estimated_amount_total = sum(lines.mapped('amount_total_prev'))
                        unit_amount_prev = estimated_amount_total / estimated_qty if estimated_qty else 0
                        lot_cost_prev = cost_total_prev / estimated_qty if estimated_qty else 0
                        marge_prev = est_marge * estimated_qty
                        line['marge'] = marge
                        line['amount_total_prev'] = estimated_amount_total
                        line['marge_prev'] = marge_prev
                        line['diff_num_amount_total'] = real_amount_total - estimated_amount_total
                        line['unit_amount'] = real_unit_amount
                        line['lot_cost'] = real_lot_cost
                        line['purchase_value'] = real_purchase_value
                        line['unit_amount_prev'] = unit_amount_prev
                        line['lot_cost_prev'] = lot_cost_prev
                        line['diff_num_unit_amount'] = real_unit_amount - unit_amount_prev
                        line['diff_num_lot_cost'] = real_lot_cost - lot_cost_prev
                        line['diff_num_marge'] = marge - marge_prev
                        line['diff_num_qty'] = real_qty - estimated_qty
                        line['cost_total_prev'] = cost_total_prev
        return res

    def get_prev_lines(self, product, user_type):
        prev_line_dir_ids = self.env['budget.budget'].search([('product_id', '=', product.id),
                                                              ('type', '=', 'prev'), ('budget_type', '=', 'sale'),
                                                              ('user_type', '=', user_type)])
        qty_prev = sum(prev_line_dir_ids.mapped('qty_prev'))
        amount_total_prev = sum(prev_line_dir_ids.mapped('amount_total_prev'))
        cost_total_prev = sum(prev_line_dir_ids.mapped('cost_total_prev'))
        marge_prev = sum(prev_line_dir_ids.mapped('marge_prev'))
        real_unit_prev_amount = amount_total_prev / qty_prev if qty_prev else 0
        real_cost_prev_amount = cost_total_prev / qty_prev if qty_prev else 0
        return qty_prev, amount_total_prev, cost_total_prev, real_unit_prev_amount, real_cost_prev_amount, marge_prev

    def compute_sale_lines(self):
        Budget = self.env['budget.budget'].search([('type', '=', 'real'), ('budget_type', '=', 'sale')])
        Budget.unlink()
        product_ids = self.env['product.product'].search([('tracking', 'in', ('lot', 'serial'))])
        for product in product_ids:
            invoice_line_ids = self.env['account.move.line'].search([('product_id', '=', product.id),
                                                                     ('move_id.move_type', '=', 'out_invoice'),
                                                                     ('quantity', '>', 0)])
            qty_prev_dir, real_prev_dir_amount_total, real_prev_dir_cost_total, real_unit_prev_dir_amount, real_cost_prev_dir_amount, marge_prev_dir = self.get_prev_lines(product, 'dir')
            qty_prev_com, real_prev_com_amount_total, real_prev_com_cost_total,  real_unit_prev_com_amount, real_cost_prev_com_amount, marge_prev_com = self.get_prev_lines(product, 'com')
            for il in invoice_line_ids:
                move_line_ids = il.mapped('sale_line_ids').mapped('move_ids'). \
                    mapped('move_line_ids')
                for ml in move_line_ids:
                    # lot_cost = mean(lot_ids.mapped('lot_cost')) if lot_ids.mapped('lot_cost') else 0
                    lot_cost = ml.lot_id.lot_cost
                    qty_invoiced = il.quantity
                    price_unit = il.price_unit
                    amount_total = (round(price_unit, 2)) * qty_invoiced
                    # cost_total = (round(lot_cost, 2)) * qty_invoiced
                    invoice_id = il.move_id
                    marge = (round(price_unit, 2) - round(lot_cost, 2)) * qty_invoiced
                    # Ecarts Prev
                    qty_prev_dir -= qty_invoiced
                    qty_prev_com -= qty_invoiced
                    real_prev_dir_amount_total -= amount_total
                    real_prev_com_amount_total -= amount_total
                    # real_prev_dir_cost_total -= cost_total
                    # real_prev_com_cost_total -= cost_total
                    marge_prev_dir -= marge
                    marge_prev_com -= marge
                    vals = {'partner_id': invoice_id.partner_id.id,
                            'product_id': product.id,
                            'qty': qty_invoiced,
                            'lot_cost': lot_cost,
                            'lot_ids': ml.lot_id.ids,
                            'unit_amount': price_unit,
                            'amount_total': amount_total,
                            'marge': marge,
                            'date': invoice_id.invoice_date,
                            'account_move_line_id': il.id,
                            'move_line_ids': move_line_ids.ids,
                            'type': 'real',
                            'budget_type': 'sale',
                            'user_type': 'com',
                            'diff_num_qty': qty_prev_com,
                            'diff_num_lot_cost': lot_cost - real_cost_prev_com_amount,
                            'diff_num_unit_amount': price_unit - real_unit_prev_com_amount,
                            'diff_num_amount_total': real_prev_com_amount_total,
                            'diff_num_marge': marge_prev_com,
                            'company_id': il.company_id.id}
                    Budget.create(vals)
                    vals['user_type'] = 'dir'
                    vals['diff_num_qty'] = qty_prev_dir
                    vals['diff_num_amount_total'] = real_prev_dir_amount_total
                    vals['diff_num_lot_cost'] = lot_cost - real_cost_prev_dir_amount
                    vals['diff_num_unit_amount'] = price_unit - real_unit_prev_dir_amount
                    vals['diff_num_marge'] = marge_prev_dir
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
