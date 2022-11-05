# -*- encoding: utf-8 -*-

from odoo import api, models,fields
from odoo.exceptions import ValidationError

class customer_payments_report_wizard(models.TransientModel):
    _name = 'customer.payments.report.wizard'

    date_start = fields.Date(string="Date début",required=False, )
    date_fin = fields.Date(string="Date fin",required=False, )

    def print_report(self):
        data = []
        partner_ids = self.env.context['active_ids']
        if self.date_start and self.date_fin and self.date_start >= self.date_fin:
            raise ValidationError('La date début doit être inférieure à la date fin')

        data.append(partner_ids[0])

        self = self.with_context(date_start=self.date_start,date_fin=self.date_fin)

        print(self.env.context,"CONTEXT")
        datas={'ids': partner_ids}

        return {
                   'type': 'ir.actions.report.xml',
                   'report_name': 'account_tres_customer.customer_payments_report',
                   'datas': datas,
                   'context': self.env.context
               }