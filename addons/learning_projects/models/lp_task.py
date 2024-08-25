from odoo import fields, models, api


class Task(models.Model):
    _name = 'lp.task'
    _description = 'LP Task'

    name = fields.Char(string='Название задачи')
    description = fields.Html(string='Описание')

    date_start = fields.Date(string='Начало')
    date_end = fields.Date(string='Конец')

    technical_specification_id = fields.Many2one('lp.technical.specification', string='Техническое задание', tracking=True)
    stages_id = fields.Many2one('lp.stages', string='Этап', tracking=True)
    assignees = fields.Many2many('res.users', string='Ответственный', tracking=True)
