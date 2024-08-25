from odoo import fields, models, api


class Terms(models.Model):
    _name = 'lp.terms'
    _description = 'Terms and abbreviations'

    name = fields.Char()
    description = fields.Text()
