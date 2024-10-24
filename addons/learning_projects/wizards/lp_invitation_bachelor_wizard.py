from odoo import fields, models, api, _
from odoo.exceptions import ValidationError



class InvitationBachelorWizard(models.TransientModel):
    _name = 'lp.send.invitation.bachelor.wizard'
    _description = 'Description'

    priority = fields.Integer(string="Приоритет", default=1, tracking=True, required=True)
    project_id = fields.Many2one('lp.project', string="Проект", tracking=True, required=True)
    resume = fields.Many2one('lp.resume', string="Резюме", required=True)  # compute='_compute_resume',
    motivation = fields.Html(string='Почему этот проект?', sanitize_attributes=False, tracking=True, required=True)

    # @api.constrains('user_id', 'project_id')
    # def _check_project_availability(self):
    #     for invitation in self:
    #         existing_invitation = self.env['lp.invitation.bachelor'].search([
    #             ('user_id', '=', invitation.user_id.id),
    #             ('project_id', '=', invitation.project_id.id),
    #             ('id', '!=', invitation.id),  # Exclude the current invitation
    #         ])
    #         if existing_invitation:
    #             raise ValidationError(_('This user has already responded to this project.'))

    def action_confirm(self):
        self.env['lp.invitation.bachelor'].sudo().create({
            'priority': self.priority,
            'project_id': self.project_id.id,
            'resume': self.resume.id,
            'motivation': self.motivation,
            'invited_status': 'waiting'
        })
        return {'type': 'ir.actions.act_window_close'}
