# -*- coding: utf-8 -*-


from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def _default_min_prix_cb(self):
        min_prix_cb = self.env['ir.config_parameter'].get_default('res.config.settings', 'min_prix_cb')
        return self.env['res.config.settings'].browse(min_prix_cb)

    has_attachment = fields.Boolean(string='Forcer les attachements')
    has_frais_bancaire = fields.Boolean(string='Forcer les frais bancaires')
    controle_cb = fields.Boolean(string=u'Contrôler le montant minimum du CB')
    min_prix_cb = fields.Float(string=u'Montant minimum')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            min_prix_cb=float(self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.min_prix_cb')),
            has_attachment=self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.has_attachment'),
            has_frais_bancaire=self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.has_frais_bancaire'),
            controle_cb=self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.controle_cb'),
        )
        return res


    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.has_attachment:
            self.env['ir.config_parameter'].sudo().set_param('account_tres_customer.has_attachment',
                                                             self.has_attachment)
        if self.has_frais_bancaire:
            self.env['ir.config_parameter'].sudo().set_param('account_tres_customer.has_frais_bancaire',
                                                             self.has_frais_bancaire)
        if self.min_prix_cb:
            self.env['ir.config_parameter'].sudo().set_param('account_tres_customer.min_prix_cb',
                                                             self.min_prix_cb)
        if self.controle_cb:
            self.env['ir.config_parameter'].sudo().set_param('account_tres_customer.controle_cb',
                                                             self.controle_cb)
        else:
            self.env['ir.config_parameter'].sudo().set_param('account_tres_customer.controle_cb',
                                                             False)
            self.env['ir.config_parameter'].sudo().set_param('account_tres_customer.min_prix_cb',
                                                             0.00)
    #
    # @api.multi
    # def set_min_prix_cb(self):
    #     return self.env['ir.config_parameter'].sudo().set_default(
    #         'res.config.settings', 'min_prix_cb', self.min_prix_cb)
