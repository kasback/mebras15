# -*- coding: utf-8 -*-
from statistics import mean

from odoo import models, fields, api
from datetime import datetime


class ResCompany(models.Model):
    _inherit = 'res.company'

    uses_account_move_sequence = fields.Boolean('Utilise une séquence de facturation pérsonalisée', default=False)


class AccountMove(models.Model):
    _inherit = 'account.move'

    intro_text = fields.Html('Texte d\'entête')
    marge = fields.Float('Marge', compute='compute_marge')
    picking_id = fields.Many2one('stock.picking', 'Livraison')
    line_lot_ids = fields.One2many('account.move.line.lot', 'move_lot_id', string='Détails des lots')
    custom_payment_method_id = fields.Selection([
        ('cheque', 'Chèque'),
        ('cash', 'Éspèces'),
        ('effet', 'Effet'),
        ('virement', 'Virement'),
        ('versement', 'Versement'),
    ],
        string=u'Mode règlement', default='cash')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(AccountMove, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                                  lazy=lazy)
        if 'marge' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_marge = 0.0
                    for record in lines:
                        total_marge += record.marge
                    line['marge'] = total_marge
        return res

    @api.model
    def create(self, vals):
        if self.env.company.uses_account_move_sequence:
            payment_date = fields.Date.today()
            self.env['ir.config_parameter'].sudo().set_param('sequence.mixin.constraint_start_date', '2023-01-01')
            if 'invoice_date' in vals and vals['invoice_date']:
                payment_date = vals['invoice_date']
            payment_date_year = datetime.strptime(str(payment_date), '%Y-%m-%d').year
            payment_date_month = '{:02d}'.format(datetime.strptime(str(payment_date), '%Y-%m-%d').month)
            name = self.env['ir.sequence'].with_context(
                ir_sequence_date=payment_date).next_by_code('account.move') + '/' + str(payment_date_month) \
                   + '/' + str(payment_date_year)
            vals['name'] = name
        return super(AccountMove, self).create(vals)

    @api.onchange('picking_id')
    def _populate_lines_from_picking(self):
        move_lines_arr = []
        self = self.with_context(check_move_validity=False)
        picking_invoice_ids = self.env['account.move'].search(
            [('picking_id', '=', self.picking_id.id), ('state', '=', 'posted')])
        for picking_line in self.picking_id.move_ids_without_package:
            qty_product_done = sum(picking_invoice_ids.invoice_line_ids.
                                   filtered(lambda line: line.product_id == picking_line.product_id).mapped('quantity'))
            qty_remaining = picking_line.quantity_done - qty_product_done
            price_subtotal = \
                picking_line.product_id.taxes_id.with_context(force_sign=self._get_tax_force_sign()).compute_all(
                    picking_line.product_id.lst_price, self.currency_id, qty_remaining, picking_line.product_id,
                    self.partner_id)['total_included']
            self.env['account.move.line'].create({
                'name': picking_line.description_picking,
                'product_id': picking_line.product_id.id,
                'price_unit': picking_line.product_id.lst_price,
                'quantity': qty_remaining,
                'company_currency_id': self.company_currency_id.id,
                'product_uom_id': picking_line.product_uom.id,
                'account_id': picking_line.product_id.property_account_income_id.id,
                'tax_ids': picking_line.product_id.taxes_id.ids,
                'move_id': self._origin.id,
                # 'price_subtotal': price_subtotal
            })
            # move_lines_arr.append(move_line)
        # self.invoice_line_ids = move_lines_arr

    def compute_marge(self):
        for rec in self:
            rec.marge = self.env['res.partner'].get_marge(rec.invoice_line_ids)

    def update_lot_lines(self):
        marge = 0
        AccountMoveLineObj = self.env['account.move.line']
        MoveLineLot = self.env['account.move.line.lot']
        MoveLineLot.search([]).unlink()
        domain = [('move_id.move_type', '=', 'out_invoice'),
                  ('move_id.state', '=', 'posted'), ('quantity', '>', '0')]
        invoice_lines = AccountMoveLineObj.search(domain)
        for line in invoice_lines:
            lot_ids = line.mapped('prod_lot_ids')
            if not lot_ids:
                continue
            for lot in lot_ids:
                lot_qty_done = 0
                move_line_ids = line.mapped('sale_line_ids.move_ids.move_line_ids'). \
                    filtered(lambda l: l.lot_id == lot)
                for ml in move_line_ids:
                    operation = (ml.qty_done * round(line.price_unit, 2)) - \
                                (round(ml.lot_id.lot_cost, 2) * ml.qty_done)
                    if ml.picking_code == "incoming":
                        lot_qty_done = -ml.qty_done
                        marge = -operation
                    elif ml.picking_code == "outgoing":
                        lot_qty_done = ml.qty_done
                        marge = operation
                    MoveLineLot.create({
                        'move_lot_id': line.move_id.id,
                        'lot_id': lot.id,
                        'product_id': lot.product_id.id,
                        'lot_cost': lot.lot_cost,
                        'price_unit': line.price_unit,
                        'qty': lot_qty_done,
                        'value': line.price_unit * lot_qty_done,
                        'marge': marge
                    })


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    num_lot = fields.Char('Numéro du lot')
    num_article = fields.Char('Num d\'Article')
    marge = fields.Float('Marge', compute='compute_marge')

    def compute_marge(self):
        for rec in self:
            rec.marge = 0
            if rec.quantity > 0 and rec.move_id.move_type == 'out_invoice' and rec.move_id.state == 'posted':
                rec.marge = self.env['res.partner'].get_marge(rec)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(AccountMoveLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                      orderby=orderby,
                                                      lazy=lazy)
        if 'marge' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    line['marge'] = sum(lines.mapped('marge'))
        return res


class AccountMoveLineLot(models.Model):
    _name = "account.move.line.lot"

    move_lot_id = fields.Many2one('account.move', 'Facture')
    product_id = fields.Many2one('product.product', 'Article')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    lot_cost = fields.Float('Coût du lot')
    price_unit = fields.Float('Prix Unitaire')
    qty = fields.Float('Quantité')
    value = fields.Float('Revenu')
    marge = fields.Float('Marge')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(AccountMoveLineLot, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                                 lazy=lazy)
        computed_fields = ['lot_cost', 'price_unit']
        for computed_field in computed_fields:
            if computed_field in fields:
                for line in res:
                    if '__domain' in line:
                        lines = self.search(line['__domain'])
                        line['lot_cost'] = mean(lines.mapped('lot_cost'))
                        line['price_unit'] = mean(lines.mapped('price_unit'))
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    total_landed_cost = fields.Monetary('Total des coûts logistiques', currency_field='company_currency_id',
                                        compute='_compute_landed_cost', default=0.0)
    total_tax_landed_cost = fields.Monetary('Total TVA coûts logistiques', currency_field='company_currency_id',
                                            compute='_compute_landed_cost', default=0.0)
    total_po_landed_cost = fields.Monetary('Total coûts logistiques compris', currency_field='company_currency_id',
                                           compute='_compute_landed_cost', default=0.0)
    company_currency_id = fields.Many2one('res.currency', string='Company Currency', required=True, readonly=True,
                                          default=lambda self: self.env.user.company_id.currency_id.id)
    amount_in_mad = fields.Monetary('Montant en DH', currency_field='company_currency_id',
                                    compute='compute_amount_in_mad')

    def compute_amount_in_mad(self):
        for rec in self:
            rec.amount_in_mad = rec.currency_id._convert(
                rec.amount_total, rec.company_currency_id, rec.company_id,
                rec.date_order or fields.Date.today())

    @api.depends('invoice_ids')
    def _compute_landed_cost(self):
        for rec in self:
            po_invoices_with_lc = rec.invoice_ids.filtered(lambda x: x.landed_costs_ids)
            lc_ids = po_invoices_with_lc.mapped('landed_costs_ids')
            rec.total_landed_cost = sum(lc_ids.mapped('amount_total'))
            rec.total_tax_landed_cost = sum(lc_ids.mapped('total_tax_landed_cost'))
            rec.total_po_landed_cost = rec.amount_in_mad + rec.total_landed_cost
