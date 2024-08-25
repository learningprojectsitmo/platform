from odoo import fields, models, api


class Specification(models.Model):
    _name = 'lp.specification'
    _description = 'Lp Specification'

    name = fields.Char(string="Техническое требование", required=True)
    development_language = fields.Text(string="Язык разработки", required=True)
    data_base = fields.Text(string="СУБД")
    customers = fields.Text(string="Потребители", required=True)
