from odoo import fields, models, api


class Stages(models.Model):
    _name = 'lp.stages'
    _description = 'Stages for Tasks'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
