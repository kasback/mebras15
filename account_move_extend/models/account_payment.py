# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(AccountPayment, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                         orderby=orderby,
                                                         lazy=lazy)
        if 'amount_company_currency_signed' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    line['amount_company_currency_signed'] = sum(
                        lines.mapped('amount_company_currency_signed')
                    )
        return res