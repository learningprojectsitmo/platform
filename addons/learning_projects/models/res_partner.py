import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

ACADEMIC_DEGREE = [
    ("bachelor", 'Бакалавр'),
    ("master", 'Магистрант'),
    ("aspirant", 'Аспирант'),
]

SCORES = [
    ('0', 'Без оценки'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5')
]

FULL_FIO_TEMPLATE = "{last_name} {name} {surname}"


class Partner(models.Model):
    _inherit = 'res.partner'
    _description = "Partner"
    _order = 'write_date desc'

    name = fields.Char(string='ФИО', tracking=True)
    firstname = fields.Char(string='Firstname', tracking=True)
    lastname = fields.Char(string='Lastname', tracking=True)

    # todo Сипаретк ФИО
    # todo hide others filds in viivs
    # todo Сделать доступ к эти поля чере import  academic_degree, number_groups

    academic_degree = fields.Selection(ACADEMIC_DEGREE, "Академическая степень")
    ear = fields.Char("Год", tracking=True)
    number_groups = fields.Char("Группа", tracking=True)
    potok = fields.Char("Поток", tracking=True, default='1')
    category_id = fields.Many2many('res.partner.category', string='Skill Stack', tracking=True)
    telegram_url = fields.Char('Телеграм', tracking=True)

    # project
    in_project = fields.Boolean("В проекте", tracking=True)
    lp_project_id = fields.Many2one('lp.project', string="Проект", readonly=True)

    score_lecturer = fields.Selection(SCORES, string='Оценка', tracking=True, default='0')
    score_master = fields.Selection(SCORES, string='Оценка от Магистра', tracking=True, default='0')
    document_ids = fields.Many2many('ir.attachment', 'lp_document_maga_ir_attachments_rel', 'partner_id', 'attachment_id', 'Отчёт', tracking=True)

    # roles
    is_admin = fields.Boolean(compute='_compute_get_is_admin', store=True)
    is_master = fields.Boolean(compute='_compute_get_is_master', store=True)
    is_bachelor = fields.Boolean(compute='_compute_get_is_bachelor', store=True)
    is_lecturer = fields.Boolean(compute='_compute_get_is_lecturer', store=True)


    @api.depends('create_date')
    def _compute_get_is_admin(self):
        for rec in self:
            user = self.env['res.users'].search([('partner_id', '=', rec.id)], limit=1)
            group_external_ids = user.get_group_external_ids()
            rec.is_admin = False
            if 'Admin' in group_external_ids:
                rec.is_admin = True

    @api.depends('create_date')
    def _compute_get_is_master(self):
        for rec in self:
            user = self.env['res.users'].search([('partner_id', '=', rec.id)], limit=1)
            group_external_ids = user.get_group_external_ids()
            rec.is_master = False
            if 'Master' in group_external_ids:
                rec.is_master = True

    @api.depends('create_date')
    def _compute_get_is_bachelor(self):
        for rec in self:
            user = self.env['res.users'].search([('partner_id', '=', rec.id)], limit=1)
            group_external_ids = user.get_group_external_ids()
            rec.is_bachelor = False
            if 'Bachelor' in group_external_ids:
                rec.is_bachelor = True

    @api.depends('create_date')
    def _compute_get_is_lecturer(self):
        for rec in self:
            user = self.env['res.users'].search([('partner_id', '=', rec.id)], limit=1)
            group_external_ids = user.get_group_external_ids()
            rec.is_lecturer = False
            if 'Lecturer' in group_external_ids:
                rec.is_lecturer = True

    def action_score_master(self):
        return {
            'name': 'Оценить бакалавра {}'.format(self.display_name),
            'type': 'ir.actions.act_window',
            'res_model': 'lp.score.master.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_author': self.id,
            }
        }

    def action_score_lecturer(self):
        return {
            'name': 'Оценить {}'.format(self.display_name),
            'type': 'ir.actions.act_window',
            'res_model': 'lp.score.lecturer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_author': self.id,
            }
        }
