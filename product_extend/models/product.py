# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from odoo.tools import float_compare


class ProductProduct(models.Model):
    _inherit = "product.product"

    marque_id = fields.Many2one('product.marque', 'Marque')
    country_id = fields.Many2one('res.country', string='Origine')
    delivered_qty = fields.Float('Quantités Livrés Glob.', compute='compute_lot_prices')
    received_qty = fields.Float('Quantités Reçus Glob.', compute='compute_lot_prices')
    value = fields.Float('Revenu Glob.', compute='compute_lot_prices')
    purchase_value = fields.Float('Prix d\'achat Glob.', compute='compute_lot_prices')
    lot_price_list = fields.Float(string='Prix unitaire Moy.', compute='compute_lot_prices')
    lot_cost = fields.Float(string='Coût Moy.', compute='compute_lot_prices')
    num_of_days = fields.Float(string='Nbr de jours', compute='compute_lot_prices')

    def compute_lot_prices(self):
        for rec in self:
            lot_ids = self.env['stock.production.lot'].search([('product_id', '=', rec.id)])
            rec.received_qty = 0
            rec.purchase_value = 0
            rec.delivered_qty = 0
            rec.value = 0
            rec.lot_price_list = 0
            rec.lot_cost = 0
            rec.lot_cost = 0
            rec.num_of_days = 0

            if lot_ids:
                rec.received_qty = sum(lot_ids.mapped('received_qty'))
                rec.purchase_value = sum(lot_ids.mapped('purchase_value'))
                rec.delivered_qty = sum(lot_ids.mapped('delivered_qty'))
                rec.value = sum(lot_ids.mapped('value'))
                rec.lot_price_list = rec.value / rec.delivered_qty if rec.delivered_qty else 0.0
                rec.lot_cost = rec.purchase_value / rec.received_qty if rec.received_qty else 0.0
                lot_w_be = len(lot_ids.filtered(lambda lot: lot.break_event_date is not False))
                rec.num_of_days = sum(lot_ids.mapped('num_of_days')) / lot_w_be if lot_w_be else 0


class ProductTemplate(models.Model):
    _inherit = "product.template"

    marque_id = fields.Many2one('product.marque', 'Marque')
    country_id = fields.Many2one('res.country', string='Origine')
    delivered_qty = fields.Float('Quantités Livrés Glob.', compute='compute_lot_prices')
    received_qty = fields.Float('Quantités Reçus Glob.', compute='compute_lot_prices')
    value = fields.Float('Revenu Glob.', compute='compute_lot_prices')
    purchase_value = fields.Float('Prix d\'achat Glob.', compute='compute_lot_prices')
    lot_price_list = fields.Float(string='Prix unitaire Moy.', compute='compute_lot_prices')
    lot_cost = fields.Float(string='Coût Moy.', compute='compute_lot_prices')
    num_of_days = fields.Float(string='Nbr de jours', compute='compute_lot_prices')

    def compute_lot_prices(self):
        for rec in self:
            lot_ids = self.env['stock.production.lot'].search([('product_id', '=', rec.id)])
            rec.received_qty = 0
            rec.purchase_value = 0
            rec.delivered_qty = 0
            rec.value = 0
            rec.lot_price_list = 0
            rec.lot_cost = 0
            rec.lot_cost = 0
            rec.num_of_days = 0

            if lot_ids:
                rec.received_qty = sum(lot_ids.mapped('received_qty'))
                rec.purchase_value = sum(lot_ids.mapped('purchase_value'))
                rec.delivered_qty = sum(lot_ids.mapped('delivered_qty'))
                rec.value = sum(lot_ids.mapped('value'))
                rec.lot_price_list = rec.value / rec.delivered_qty if rec.delivered_qty else 0.0
                rec.lot_cost = rec.purchase_value / rec.received_qty if rec.received_qty else 0.0
                lot_w_be = len(lot_ids.filtered(lambda lot: lot.break_event_date is not False))
                rec.num_of_days = sum(lot_ids.mapped('num_of_days')) / lot_w_be if lot_w_be else 0


class StockProductionLotTag(models.Model):
    _name = "stock.production.lot.tag"

    name = fields.Char('Nom')


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    delivered_qty = fields.Float('Quantités Livrés', compute='_compute_delivered_qty')
    received_qty = fields.Float('Quantités Reçus', compute='_compute_delivered_qty')
    forced_received_qty = fields.Float('Forcer Quantités Reçus')
    target_qty = fields.Float('Quantités Rechérché', compute='compute_lot_price_list')
    remaining_qty = fields.Float('Quantités Restante', compute='_compute_delivered_qty')
    value = fields.Float('Revenu', compute='_compute_delivered_qty')
    purchase_value = fields.Float('Prix d\'achat', compute='_compute_delivered_qty')
    lot_price_list = fields.Float(string='Prix unitaire', compute='compute_lot_price_list')
    lot_cost = fields.Float(string='Coût', compute='_compute_delivered_qty')
    lot_cost_forced = fields.Float(string='Forcer Coût')
    marge = fields.Float(string='Marge', compute='compute_lot_price_list')
    marge_in_percent = fields.Float(string='% Marge', compute='compute_lot_price_list')
    break_event_date = fields.Date('Date break Event', compute='compute_break_event_date')
    num_of_days = fields.Float(string='Nbr de jours', compute='compute_break_event_date')
    tag_ids = fields.Many2many('stock.production.lot.tag', string='Étiquettes')
    # pa+pf
    invoiced_price = fields.Float(string='PF')
    invoiced_marge = fields.Float(string='Marge', compute='compute_pa_pf_vals')
    invoiced_marge_in_percent = fields.Float(string='% Marge', compute='compute_pa_pf_vals')
    invoiced_value = fields.Float(string='Prix Facturation', compute='compute_pa_pf_vals')
    difference = fields.Float(string='Difference', compute='compute_pa_pf_vals')
    pa_pf_tag_ids = fields.Many2many('stock.production.lot.tag', 'pa_pf_lot_tags', string='Étiquettes')
    # Chiffrage
    marge_chiffrage = fields.Float(string='Marge', compute='compute_chiffrage_vals')
    marge_chiffrage_in_percent = fields.Float(string='% Marge', compute='compute_chiffrage_vals')
    invoiced_qty = fields.Float(string='Quantité facturé')
    remaining_qty_chiffrage = fields.Float(string='Quantité en stock', compute='compute_chiffrage_vals')
    total_invoiced_chiffrage = fields.Float(string='Total Facturé', compute='compute_chiffrage_vals')
    total_in_stock_chiffrage = fields.Float(string='Total en stock', compute='compute_chiffrage_vals')
    chiffrage_tag_ids = fields.Many2many('stock.production.lot.tag', 'chiffrage_lot_tags', string='Étiquettes')

    def compute_chiffrage_vals(self):
        for rec in self:
            rec.marge_chiffrage = rec.invoiced_price - rec.lot_cost
            rec.marge_chiffrage_in_percent = rec.invoiced_price / rec.lot_cost if rec.lot_cost else 0
            rec.remaining_qty_chiffrage = rec.received_qty - rec.invoiced_qty
            rec.total_invoiced_chiffrage = rec.invoiced_price * rec.invoiced_qty
            rec.total_in_stock_chiffrage = rec.remaining_qty_chiffrage * rec.lot_cost

    def compute_pa_pf_vals(self):
        for rec in self:
            rec.invoiced_marge = rec.lot_price_list - rec.invoiced_price
            rec.invoiced_marge_in_percent = rec.lot_price_list / rec.invoiced_price if rec.invoiced_price else 0
            rec.invoiced_value = rec.invoiced_price * rec.delivered_qty
            rec.difference = rec.value - rec.invoiced_value

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(StockProductionLot, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                         orderby=orderby,
                                                         lazy=lazy)
        computed_fields = ['delivered_qty', 'received_qty', 'purchase_value', 'value', 'marge', 'marge_in_percent',
                           'remaining_qty', 'invoiced_marge',
                           'invoiced_marge_in_percent',
                           'invoiced_value',
                           'difference',
                           'remaining_qty_chiffrage',
                           'total_invoiced_chiffrage',
                           'total_in_stock_chiffrage',
                           ]
        for computed_field in computed_fields:
            if computed_field in fields:
                for line in res:
                    if '__domain' in line:
                        lines = self.search(line['__domain'])
                        total_marge = 0.0
                        total_sale = 0.0
                        total_purchase = 0.0
                        total_delivered_qty = 0.0
                        total_received_qty = 0.0
                        total_remaining_qty = 0.0
                        total_invoiced_marge = 0.0
                        total_invoiced_marge_in_percent = 0.0
                        total_invoiced_value = 0.0
                        total_difference = 0.0
                        total_remaining_qty_chiffrage = 0.0
                        total_total_invoiced_chiffrage = 0.0
                        total_total_in_stock_chiffrage = 0.0
                        for record in lines:
                            total_delivered_qty += record.delivered_qty
                            total_received_qty += record.received_qty
                            total_purchase += record.purchase_value
                            total_sale += record.value
                            total_remaining_qty += record.remaining_qty
                            total_invoiced_marge += record.invoiced_marge
                            total_invoiced_marge_in_percent += record.invoiced_marge_in_percent
                            total_invoiced_value += record.invoiced_value
                            total_difference += record.difference
                            total_remaining_qty_chiffrage += record.remaining_qty_chiffrage
                            total_total_invoiced_chiffrage += record.total_invoiced_chiffrage
                            total_total_in_stock_chiffrage += record.total_in_stock_chiffrage
                            total_marge += record.value - record.purchase_value
                        total_marge_percent = ((total_sale / total_purchase) - 1) * 100 if total_purchase else 0
                        line['delivered_qty'] = total_delivered_qty
                        line['received_qty'] = total_received_qty
                        line['purchase_value'] = total_purchase
                        line['value'] = total_sale
                        line['marge'] = total_marge
                        line['marge_in_percent'] = total_marge_percent
                        line['invoiced_marge'] = total_invoiced_marge
                        line['invoiced_marge_in_percent'] = total_invoiced_marge_in_percent
                        line['invoiced_value'] = total_invoiced_value
                        line['difference'] = total_difference
                        line['remaining_qty_chiffrage'] = total_remaining_qty_chiffrage
                        line['total_invoiced_chiffrage'] = total_total_invoiced_chiffrage
                        line['total_in_stock_chiffrage'] = total_total_in_stock_chiffrage
        return res

    def compute_break_event_date(self):
        StockMoveLine = self.env['stock.move.line']
        for rec in self:
            rec.break_event_date = False
            rec.num_of_days = 0
            target = rec.target_qty
            current = 0.0
            customers_location_id = self.env.ref('stock.stock_location_customers')

            move_line_ids = StockMoveLine.search([('lot_id', '=', rec.id),
                                                  '|',
                                                  ('location_id', '=', customers_location_id.id),
                                                  ('location_dest_id', '=', customers_location_id.id)
                                                  ], order='date ASC')
            if sum(move_line_ids.mapped('qty_done_signed')) < target:
                break
            can_update_be = True
            for ml in move_line_ids:
                current += ml.qty_done_signed
                if current < target:
                    can_update_be = True
                    rec.break_event_date = False
                elif current >= target and can_update_be:
                    rec.break_event_date = ml.date
                    can_update_be = False
            if rec.break_event_date:
                rec.num_of_days = (rec.break_event_date - rec.create_date.date()).days

    def _compute_delivered_qty(self):
        for rec in self:
            rec.delivered_qty = 0.0
            rec.remaining_qty = 0.0
            rec.purchase_value = 0.0
            rec.value = 0.0
            rec.lot_cost = 0.0
            lot_cost = 0.0
            customers_location_id = self.env.ref('stock.stock_location_customers')
            suppliers_location_id = self.env.ref('stock.stock_location_suppliers')
            move_lines = self.env['stock.move.line'].search([('picking_id.state', '=', 'done'),
                                                             ('lot_id', '=', rec.id)])
            outgoing_move_ids = move_lines.filtered(lambda l: l.picking_code == 'outgoing'
                                                              and l.location_dest_id == customers_location_id)
            incoming_move_ids = move_lines.filtered(lambda l: l.picking_code == 'incoming'
                                                              and l.location_id == suppliers_location_id)
            returned_customer_move_ids = move_lines.filtered(lambda l: l.picking_code == 'incoming'
                                                                       and l.location_id == customers_location_id)
            returned_supplier_move_ids = move_lines.filtered(lambda l: l.picking_code == 'outgoing'
                                                                       and l.location_dest_id == suppliers_location_id)
            for p in outgoing_move_ids:
                rec.value += p.qty_done * p.move_id.sale_line_id.price_unit
            for p in returned_customer_move_ids:
                rec.value -= p.qty_done * p.move_id.sale_line_id.price_unit
            for p in incoming_move_ids:
                lot_cost = (p.move_id.purchase_line_id.real_purchase_price +
                            (
                                        p.move_id.purchase_line_id.order_id.total_landed_cost / p.move_id.purchase_line_id.qty_received)) * 1.2 if p.move_id.purchase_line_id.qty_received else 0
            rec.lot_cost = rec.lot_cost_forced or lot_cost
            rec.delivered_qty = sum(outgoing_move_ids.mapped('qty_done')) - sum(
                returned_customer_move_ids.mapped('qty_done'))
            received_qty = sum(incoming_move_ids.mapped('qty_done')) - sum(
                returned_supplier_move_ids.mapped('qty_done'))
            rec.received_qty = rec.forced_received_qty or received_qty
            rec.purchase_value = rec.lot_cost * rec.received_qty
            rec.remaining_qty = rec.received_qty - rec.delivered_qty

    def compute_lot_price_list(self):
        for rec in self:
            rec.lot_price_list = rec.value / rec.delivered_qty if rec.delivered_qty else 0.0
            rec.target_qty = rec.purchase_value / rec.lot_price_list if rec.lot_price_list else 0.0
            rec.marge = rec.lot_price_list - rec.lot_cost
            rec.marge_in_percent = ((rec.value / rec.purchase_value) - 1) * 100 if rec.purchase_value else 0.0


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    num_du_lot = fields.Char('Numéro du lot')
    num_art = fields.Char('Num d\'Article')

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        res.update({
            'num_du_lot': self.num_du_lot,
            'num_art': self.num_art,
            'designation': self.name,
        })
        return res


class StockRuleInherit(models.Model):
    _inherit = 'stock.rule'

    num_du_lot = fields.Char('Numéro du lot')
    num_art = fields.Char('Num d\'Article')

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        res = super(StockRuleInherit, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id,
                                                                   name, origin, values, group_id)

        order_line = self.env['sale.order.line'].browse(res.get('sale_line_id'))
        res['num_du_lot'] = order_line.num_du_lot
        res['num_art'] = order_line.num_art
        res['designation'] = order_line.name
        return res


class ProductMarque(models.Model):
    _name = "product.marque"

    name = fields.Char('Nom')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    intro_text = fields.Html('Texte d\'entête')


class StockMove(models.Model):
    _inherit = 'stock.move'

    num_du_lot = fields.Char('Numéro du lot')
    num_art = fields.Char('Num d\'Article')
    designation = fields.Char('Désignation')

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        # apply putaway
        location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id,
            'picking_id': self.picking_id.id,
            'company_id': self.company_id.id,
            'num_du_lot': self.num_du_lot or False,
            'num_art': self.num_art or False,
            'designation': self.description_picking or False,
        }
        if quantity:
            uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom,
                                                                    rounding_method='HALF-UP')
            uom_quantity_back_to_product_uom = self.product_uom._compute_quantity(uom_quantity, self.product_id.uom_id,
                                                                                  rounding_method='HALF-UP')
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                vals = dict(vals, product_uom_qty=uom_quantity)
            else:
                vals = dict(vals, product_uom_qty=quantity, product_uom_id=self.product_id.uom_id.id)
        if reserved_quant:
            vals = dict(
                vals,
                location_id=reserved_quant.location_id.id,
                lot_id=reserved_quant.lot_id.id or False,
                package_id=reserved_quant.package_id.id or False,
                owner_id=reserved_quant.owner_id.id or False,

            )
        return vals


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    intro_text = fields.Html('Texte d\'entête')

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        for do_pick in self.picking_ids:
            do_pick.write({'intro_text': self.intro_text})

        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    num_du_lot = fields.Char('Numéro du lot')
    num_art = fields.Char('Num d\'Article')
    designation = fields.Char('Désignation')
    partner_id = fields.Many2one('res.partner', related='picking_id.partner_id', string='Partenaire')
    qty_done_signed = fields.Float('Quantité comptée', compute='compute_qty_done_signed', store=True)

    def _get_aggregated_product_quantities(self, **kwargs):
        """ Returns a dictionary of products (key = id+name+description+uom) and corresponding values of interest.

        Allows aggregation of data across separate move lines for the same product. This is expected to be useful
        in things such as delivery reports. Dict key is made as a combination of values we expect to want to group
        the products by (i.e. so data is not lost). This function purposely ignores lots/SNs because these are
        expected to already be properly grouped by line.

        returns: dictionary {product_id+name+description+uom: {product, name, description, qty_done, product_uom}, ...}
        """
        aggregated_move_lines = {}
        for move_line in self:
            name = move_line.product_id.display_name
            description = move_line.move_id.description_picking
            if description == name or description == move_line.product_id.name:
                description = False
            uom = move_line.product_uom_id
            line_key = str(move_line.product_id.id) + "_" + name + (description or "") + "uom " + str(uom.id)

            if line_key not in aggregated_move_lines:
                aggregated_move_lines[line_key] = {'name': name,
                                                   'description': description,
                                                   'qty_done': move_line.qty_done,
                                                   'product_uom': uom.name,
                                                   'product': move_line.product_id,
                                                   'num_du_lot': move_line.num_du_lot,
                                                   'num_art': move_line.num_art,
                                                   'designation': move_line.designation,
                                                   'default_code': move_line.product_id.default_code,
                                                   'marque': move_line.product_id.marque_id.name,
                                                   'origine': move_line.product_id.country_id.name,
                                                   }
            else:
                aggregated_move_lines[line_key]['qty_done'] += move_line.qty_done
        return aggregated_move_lines

    @api.depends('qty_done')
    def compute_qty_done_signed(self):
        customers_location_id = self.env.ref('stock.stock_location_customers')
        for rec in self:
            rec.qty_done_signed = -rec.qty_done if rec.location_id == customers_location_id else rec.qty_done


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    product_standard_price = fields.Float(string='Prix unitaire', compute='compute_product_standard_price')
    lot_ids = fields.Many2many('stock.production.lot', related='stock_move_id.lot_ids', string='numéro de lot')

    @api.depends('value', 'quantity')
    def compute_product_standard_price(self):
        for rec in self:
            rec.product_standard_price = rec.value / rec.quantity if rec.quantity else 0.0

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(StockValuationLayer, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                          orderby=orderby,
                                                          lazy=lazy)
        if 'product_standard_price' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    total_product_standard_price = 0.0
                    for record in lines:
                        total_product_standard_price += record.product_standard_price
                    line['product_standard_price'] = total_product_standard_price
        return res
