from odoo import models, fields, api
from odoo.exceptions import ValidationError

from .utils import create_notification

PROJECT_STATUS = [
    ('Unconfirmed', 'Не подтверждён'),
    ('OnApproval', 'На утверждении темы'),
    ('TeamFormation', 'Формирование команды'),
    ('CreationTex', 'Создание ТЗ'),
    ('OnApprovalTex', 'На утверждении ТЗ'),
    ('Teamwork', 'Работа команды'),
    ('Ready to defend', 'Готовы к защите'),
    ('Past', 'C оценкой')
]


class LpProject(models.Model):
    _name = 'lp.project'
    _inherit = ['mail.thread']
    _description = 'Учебные проекты'

    # Project info
    name = fields.Char(string='Название проекта', tracking=True, required=True)
    description = fields.Html(string='Описание проекта', sanitize_attributes=False, tracking=True, required=True)
    required_participants = fields.Html(string='Необходимые участники', sanitize_attributes=False, tracking=True, required=True)
    logo = fields.Image(string='Project logo')

    status = fields.Selection(PROJECT_STATUS, string='Статус', readonly=True, tracking=True, default='Unconfirmed')
    author = fields.Many2one('res.partner', string='Автор', compute='compute_author', readonly=True, tracking=True)

    project_info = fields.Many2many('ir.attachment', 'lp_project_info_document_ir_attachments_rel',
                                    'lp_project_id', 'attachment_id', 'Project info', tracking=True, copy=True)

    # Accept Project info by lecturer
    confirmed_id = fields.Many2one('res.partner', string='Подтверждено', readonly=True, tracking=True)

    # project
    project = fields.Many2one('project.project', string='Канбан', readonly=True, tracking=True)
    stage_id = fields.Many2one(related='project.stage_id', string='Статус', readonly=True, tracking=True)
    tag_ids = fields.Many2many(related='project.tag_ids', string='Навыки', tracking=True)
    # note = fields.Many2many('note.note', string='Записки', tracking=True)

    technical_specification  = fields.Many2one('lp.technical.specification', string='ТЗ', readonly=True, tracking=True)
    # Team
    message_partner_ids = fields.Many2many(related='project.message_partner_ids', string='message_follower_ids', readonly=True, tracking=True)
    max_col_users = fields.Integer(string='Максимальное количество участников', default=5, readonly=True, tracking=True)
    current_value_users = fields.Integer(string='Текущее количество участников', default=0, readonly=True, tracking=True)

    @api.depends('max_col_users', 'current_value_users')
    def _compute_is_all_invited(self):
        for record in self:
            record.is_all_invited = record.current_value_users >= record.max_col_users
            if record.is_all_invited:
                record.sudo().write({'status': 'CreationTex'})
                if not self.technical_specification:
                    current_user = self.env.user.partner_id
                    message_partner_ids = record.message_partner_ids.filtered(lambda partner: partner != current_user)
                    technical_specification = self.env['lp.technical.specification'].sudo().create({
                        'name': record.name,
                        'author': record.author.id,
                        'message_partner_ids': message_partner_ids,
                        'create_uid': record.author.user_id.id
                    })
                    record.sudo().write({'technical_specification': technical_specification.id})

                for invitation_id in record.invitation_bachelor_ids.ids:
                    invitation = self.env['lp.invitation.bachelor'].browse(invitation_id)
                    if invitation.invited_status == 'waiting':
                        invitation.sudo().write({'invited_status': 'invited_all'})

    is_all_invited = fields.Boolean('Is All invited', compute='_compute_is_all_invited', store=True, readonly=True, tracking=True)

    # Invitation Bachelor
    invitation_bachelor_ids = fields.One2many('lp.invitation.bachelor', 'project_id', domain=[('invited_status', '!=', 'draft')], string='Project info', readonly=True, tracking=True)

    @api.model
    def create(self, vals):
        self.validate_count_creations()
        lp = super(LpProject, self).create(vals)
        lp.author.sudo().write({'in_project': True, 'lp_project_id': lp.id})
        return lp

    def write(self, vals):
        return super(LpProject, self).write(vals)

    def validate_count_creations(self):
        project = self.env['lp.project'].search([('create_uid', '=', self.env.uid)])
        if len(project) > 0:
            raise ValidationError('Магистр может создать только 1 проект')

    @api.depends('author')
    def compute_author(self):
        for rec in self:
            author = self.env['res.users'].browse(rec.create_uid.id).partner_id
            rec.author = author.id

    def send_confirm_project_tex(self):
        self.write({'status': 'OnApprovalTex'})

    def send_confirm_project(self):
        params = self.env['ir.config_parameter'].sudo()
        project_stage_2_id = int(params.get_param('project_stage_2_id'))
        if not self.project:
            project = self.env['project.project'].sudo().create({
                'name': self.name,
                'stage_id': project_stage_2_id
            })
            project.write({'message_partner_ids': [(4, self.author.id)]})
            self.write({'project': project.id, 'status': 'OnApproval'})
        else:
            self.write({'status': 'OnApproval'})

    def set_work_project(self):
        for project in self:
            project.sudo().write({'max_col_users': project.current_value_users})

    def confirm_project(self):
        partner = self.env['res.users'].browse(self.env.uid).partner_id
        return self.write({'status': 'TeamFormation',
                           'confirmed_id': partner.id})

    def confirm_project_tex(self):
        partner = self.env['res.users'].browse(self.env.uid).partner_id
        for project in self:
            project.technical_specification.sudo().write({'status': 'Approval', 'confirmed_id': partner.id})

    def action_view_tasks(self):
        project_id = self.project.id
        return self.project.action_custom_view_tasks(project_id)

    def action_team_is_ready(self):
        self.write({'status': 'Ready to defend'})

    def create_invitation_bachelor(self):
        if self and self.invitation_bachelor_ids.filtered(lambda inv: inv.user_id.id == self.env.uid):
            notification_type = 'warning'
            title = 'Ошибка'
            message = 'Приглашение уже отправлено'
            return create_notification(notification_type, title, message)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lp.send.invitation.bachelor.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
            },
            'options': {'hide_save': True}
        }
