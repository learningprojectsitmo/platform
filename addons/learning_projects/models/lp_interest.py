from odoo import models, fields, api
from random import randint
from odoo.exceptions import ValidationError


class Interest(models.Model):
    _name = 'lp.interest'
    _description = "Область интересов пользователя"
    _order = 'write_date desc'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char('Интересы', required=True, translate=True)
    color = fields.Integer(string='Цвет', default=_get_default_color)

    @api.model
    def create(self, vals):
        vals.update({"name": vals.get("name").lower().capitalize()})
        return super(Interest, self).create(vals)

    @api.constrains('name')
    def _check_duplicate_name(self):
        for record in self:
            if self.search_count([('id', '!=', record.id), ('name', '=', record.name)]) > 0:
                raise ValidationError("Interest with this name already exists.")
            if len(record.name) > 30:
                raise ValidationError("Interest name max size 20 chars.")
