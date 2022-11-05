# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    real_purchase_price = fields.Monetary('Prix Effectif', currency_field='currency_id')
