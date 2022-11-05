# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Account(models.Model):
    _inherit = "account.account"

    @api.model
    def create(self, vals):
        print('vals', vals['group_id'])
        if not vals['group_id']:
            digits = vals['code'][0:3]
            group_id = self.env['account.group'].search([('code_prefix_start', '=', digits)])
            vals['group_id'] = group_id.id
        res = super(Account, self).create(vals)

        return res
