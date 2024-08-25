from odoo import fields, models, api
from odoo.tools import config as odoo_conf


class Stages(models.Model):
    _name = 'lp.stages'
    _description = 'Stages for Tasks'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
