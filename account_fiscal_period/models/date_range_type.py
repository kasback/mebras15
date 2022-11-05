# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    fiscal_period = fields.Boolean(string='Is fiscal period ?', default=False)

    def unlink(self):
        """
        Cannot delete a date_range_type with 'fiscal_period' flag = True
        """
        for rec in self:
            if rec.fiscal_period:
                raise exceptions.ValidationError(
                    (u'Vous ne pouvez pas supprimer le type de période fiscale"')
                )
            else:
                super(DateRangeType, rec).unlink()
