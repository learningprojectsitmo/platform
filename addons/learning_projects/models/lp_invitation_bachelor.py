from odoo import models, fields, api
from odoo.exceptions import ValidationError

STATUS = [
    ("draft", "Черновик"),
    ("waiting", "В ожидании"),
    ("invited_all", "Проект уже сформирован"),
    ("invited", "Приглашен"),
    ("invited_for_other_priority", "Приглашен по другому приоритету"),
]


def create_notification(notification_type, title, message):
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': title,
            'message': message,
            'sticky': False,
            'type': notification_type,
            'fadeout': 'slow',
            'next': {
                'type': 'ir.actions.act_window_close',
            }
        }
    }


class InvitationBachelor(models.Model):
    _name = 'lp.invitation.bachelor'
    _description = 'Приглашения бакалавра'
    _inherit = ['mail.thread']
    _order = 'priority asc'

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

    # bachelor
    priority = fields.Integer(string="Приоритет", default=1,  tracking=True, required=True)
    project_id = fields.Many2one('lp.project', string="Проект",  tracking=True, required=True)
    is_all_invited = fields.Boolean(related='project_id.is_all_invited', string="is_all_invited")
    resume = fields.Many2one('lp.resume', string="Резюме", required=True)  # compute='_compute_resume',
    resume_author = fields.Many2one(related='resume.author', string="Отправитель", store=True, readonly=True)
    number_groups = fields.Char(related='resume_author.number_groups', string="Группа", readonly=True)
    motivation = fields.Html(string='Почему этот проект?', sanitize_attributes=False, tracking=True, required=True)

    invited_by = fields.Many2one('res.partner', string="Приглашён кем", readonly=True, tracking=True)
    invited_status = fields.Selection(STATUS, string="Статус", default="draft", readonly=True, tracking=True)

    @api.model
    def create(self, vals):
        self.validate_count_creations()
        return super(InvitationBachelor, self).create(vals)

    def write(self, vals):
        self.change_priority(vals.get("priority"))
        return super(InvitationBachelor, self).write(vals)

    @api.depends('resume')
    def _compute_resume(self):
        for rec in self:
            resume = self.env['lp.resume'].search([('create_uid', '=', rec.create_uid.id)])
            rec.resume = resume.id

    @api.constrains('priority')
    def _check_priority(self):
        priority = self.priority
        if priority != 1 and priority != 2:
            raise ValidationError('Priority 1 or 2 ' + str(priority))

    @api.onchange('project_id')
    def onchange_project_id(self):
        domain = []
        invitations = self.env['lp.invitation.bachelor'].search([('create_uid', '=', self.env.uid)])
        for invitation in invitations:
            if invitation is not None:
                domain.append(('id', '!=', invitation.project_id.id))
        return {'domain': {'project_id': domain}}

    @api.constrains('user_id')
    def _check_user(self):
        for record in self:
            if record.user_id and record.user_id != self.env.user:
                raise ValidationError("Вы не можете изменять записи других пользователей")

    def change_priority(self, priority):
        invitation = self.env['lp.invitation.bachelor'].search([('create_uid', '=', self.env.uid)], limit=1)
        if invitation is not None:
            if priority == 1 and invitation.priority != 2:
                invitation.write({'priority': 2})
            elif priority == 2 and invitation.priority != 1:
                invitation.write({'priority': 1})

    def validate_count_creations(self):
        user = self.env.user
        invitations = self.env['lp.invitation.bachelor'].search([('create_uid', '=', self.env.uid)])
        if user.has_group('learning_projects.lp_group_bachelor') and len(invitations) > 1:
            raise ValidationError("Бакалавр может создать только 2 приглашения")

    @api.constrains('invited_status', 'project_id', 'resume')
    def _check_status(self):
        for record in self:
            befo_invitation = self.env['lp.invitation.bachelor'].search([('id', '=', record.id)], limit=1)
            if record.user_id == self.env.user and record.invited_status in ['invited', 'invited_for_other_priority'] and befo_invitation.invited_status == 'waiting':
                raise ValidationError("Вы не можете изменять или удалять свои записи со статусом 'ожидание'")

    def action_confirm_invitation(self):
        resume_author = self.resume_author.id
        lp_p = self.project_id
        if lp_p.is_all_invited:
            raise ValidationError('Вы уже пригласили {max_col_users}'.format(max_col_users=lp_p.max_col_users))

        lp_p.project.message_subscribe(partner_ids=[self.resume_author.id])
        new_current_value_users = lp_p.current_value_users + 1
        lp_p.write({'current_value_users': new_current_value_users})

        self.resume_author.sudo().write({'in_project': True, 'lp_project_id': lp_p.id})

        self.sudo().write({
            'invited_status': 'invited',
            'invited_by': self.env['res.users'].browse(self.env.uid).partner_id,
        })

        invitation = self.env['lp.invitation.bachelor'].search([('resume_author', '=', resume_author), ('id', '!=', self.id)], limit=1)
        if invitation is not None:
            invitation.sudo().write({'invited_status': 'invited_for_other_priority'})

    def action_reject_invitation(self):
        resume_author = self.resume_author.id
        lp_p = self.project_id
        #if lp_p.is_all_invited:
        #    raise ValidationError('Вы уже пригласили {max_col_users}'.format(max_col_users=lp_p.max_col_users))

        lp_p.project.message_unsubscribe(partner_ids=[self.resume_author.id])

        new_current_value_users = lp_p.current_value_users - 1
        lp_p.project.sudo().write({'with_out': True})
        if lp_p.is_all_invited:
            lp_p.sudo().write({'current_value_users': new_current_value_users,
                    'status': 'TeamFormation',
                    "is_all_invited": False})

            for invitation_id in lp_p.invitation_bachelor_ids.ids:
                invitation = self.env['lp.invitation.bachelor'].browse(invitation_id)
                if invitation.invited_status == 'invited_all':
                    invitation.sudo().write({'invited_status': 'waiting'})
        else:
            lp_p.sudo().write({'current_value_users': new_current_value_users})

        lp_p.project.sudo().write({'with_out': False})

        self.resume_author.sudo().write({'in_project': False, 'lp_project_id': False})
        self.sudo().write({
            'invited_status': 'waiting',
            'invited_by': False,
        })

        invitation = self.env['lp.invitation.bachelor'].search([('resume_author', '=', resume_author), ('id', '!=', self.id)], limit=1)
        if invitation is not None:
            invitation.sudo().write({'invited_status': 'waiting'})

    def action_send_invitation(self):
        for invitation in self:
            show_warning = False
            if invitation.invited_status == "draft":
                invitation.sudo().write({'invited_status': 'waiting'})
            else:
                show_warning = True

            notification_type = 'warning' if show_warning else 'success'
            title = 'Ошибка' if show_warning else 'Успешно'
            message = 'Вы не можите это сделать' if show_warning else 'Приглашение отправленно'
            return create_notification(notification_type, title, message)

    def action_draft_invitation(self):
        for invitation in self:
            show_warning = False
            if invitation.invited_status == "waiting" or invitation.invited_status == "invited_all":
                invitation.sudo().write({'invited_status': 'draft'})
            else:
                show_warning = True

            notification_type = 'warning' if show_warning else 'success'
            title = 'Ошибка' if show_warning else 'Успешно'
            message = 'Вы не можите это сделать' if show_warning else 'Приглашение стало черновиком'
            return create_notification(notification_type, title, message)

    def name_get(self):
        result = []
        for record in self:
            result.append((record['id'], record.resume.name))
        return result
