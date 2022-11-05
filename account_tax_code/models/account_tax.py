# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    code = fields.Integer('Code')


class AccountTaxTemplate(models.Model):
    _inherit = 'account.tax.template'

    code = fields.Integer('Code')

    def _get_tax_vals(self, company, tax_template_to_tax):
        val = super(AccountTaxTemplate,self)._get_tax_vals(company, tax_template_to_tax)
        val['code'] = self.code
        return val
