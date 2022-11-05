# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class PartnerDso(models.Model):
    _name = 'res.partner.dso'

    partner_id = fields.Many2one('res.partner', 'Partenaire')
    partner_dso = fields.Float(string='DSO')
    num_of_days = fields.Float(string='Nbr de jours')
    target_amount = fields.Float(string='Montant Target')
    recovery_amount = fields.Float(string='Recouvrement')
    date = fields.Date(string='Date')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env['res.company']._company_default_get('res.partner.dso'),
                                 string='Société')

    def compute_partner_dso(self):
        partners = self.env['res.partner'].search([])
        AccountMove = self.env['account.move']
        PartnerDso = self.env['res.partner.dso']
        for partner in partners:
            unpaid_invoices = AccountMove.search([('move_type', '=', 'out_invoice'),
                                                        ('partner_id', '=', partner.id),
                                                        ('payment_state', 'in', ('not_paid', 'partial')),
                                                        ('company_id', '=', 1),
                                                  ],
                                                       order='invoice_date ASC')
            amount_due = partner.total_overdue
            amount_total = sum(unpaid_invoices.mapped('amount_total_signed'))
            target_amount = 0
            partner_dso = 0
            num_of_days = 0
            if unpaid_invoices and unpaid_invoices[0].invoice_date:
                num_of_days = (fields.Date().today() - unpaid_invoices[0].invoice_date).days
                partner_dso = (amount_due / amount_total) * num_of_days
                target_amount = (partner.dso_target * amount_total) / num_of_days if num_of_days else 0
            recovery_amount = amount_due - target_amount
            if partner.dso_target > partner_dso:
                target_amount = 0
                recovery_amount = partner.total_overdue
            if partner.total_overdue < 0:
                target_amount = 0
                recovery_amount = 0
            if partner_dso < 0:
                partner_dso = 0
            PartnerDso.create({
                'date': fields.Date().today(),
                'partner_id': partner.id,
                'partner_dso': partner_dso,
                'target_amount': target_amount,
                'recovery_amount': recovery_amount,
                'num_of_days': num_of_days,
                'company_id': 1,
            })
            partner.write({
                'partner_dso': partner_dso,
                'target_amount': target_amount,
                'recovery_amount': recovery_amount,
                'num_of_days': num_of_days,
            })

