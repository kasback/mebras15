# -*- encoding: utf-8 -*-
from odoo import models, fields, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def name_get(self):
        return [
            (
                rec.id,
                "{} - {} - {}".format(
                    rec.picking_id.name, rec.product_id.name, rec.lot_id.name
                ),
            )
            for rec in self
        ]
