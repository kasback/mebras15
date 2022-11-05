# -*- encoding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    dso_global_desired = fields.Float(string='DSO voulu')
