import ast
from odoo.exceptions import ValidationError
from odoo.tools import config as odoo_conf
from odoo import api, fields, models, _

class Project(models.Model):
    _inherit = "project.project"

    # Create team chat
    # mail.channel
    with_out = fields.Boolean('Is All invited', readonly=True, default=False)

    # visibility all for followers
    privacy_visibility = fields.Selection([
        ('followers', 'Invited internal users'),
        ('employees', 'All internal users'),
        ('portal', 'Invited portal users and all internal users'),
    ],
        string='Visibility', required=True,
        default='followers', readonly=True,
        help="People to whom this project and its tasks will be visible.\n\n"
             "- Invited internal users: when following a project, internal users will get access to all of its tasks without distinction. "
             "Otherwise, they will only get access to the specific tasks they are following.\n "
             "A user with the project > administrator access right level can still access this project and its tasks, even if they are not explicitly part of the followers.\n\n"
             "- All internal users: all internal users can access the project and all of its tasks without distinction.\n\n"
             "- Invited portal users and all internal users: all internal users can access the project and all of its tasks without distinction.\n"
             "When following a project, portal users will get access to all of its tasks without distinction. Otherwise, they will only get access to the specific tasks they are following.\n\n"
             "When a project is shared in read-only, the portal user is redirected to their portal. They can view the tasks, but not edit them.\n"
             "When a project is shared in edit, the portal user is redirected to the kanban and list views of the tasks. They can modify a selected number of fields on the tasks.\n\n"
             "In any case, an internal user with no project access rights can still access a task, "
             "provided that they are given the corresponding URL (and that they are part of the followers if the project is private).")

    @api.model
    def create(self, vals):
        return super(Project, self).create(vals)

    def write(self, vals):
        if not self.with_out:
            user = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
            if ((user.partner_id.is_master and vals.get('stage_id') == int(odoo_conf['project_stage_3_id'])) or (user.partner_id.is_master and vals.get('stage_id') == int(odoo_conf['project_stage_6_id']))):
                raise ValidationError("Это может сделать только преподаватель")
        return super(Project, self).write(vals)

    def action_view_tasks(self):
        action = super(Project, self).action_view_tasks()
        return action

    def action_custom_view_tasks(self, project):
        action = self.env['ir.actions.act_window'].with_context({'active_id': project.id})._for_xml_id('project.act_project_project_2_project_task_all')
        action['display_name'] = _("%(name)s", name='Доска')
        context = action['context'].replace('active_id', str(project.id))
        context = ast.literal_eval(context)
        context.update({
            'create': self.project.active,
            'active_test': self.project.active
        })
        action['context'] = context
        return action


class Task(models.Model):
    _inherit = "project.task"

    user_ids = fields.Many2many('res.users', relation='project_task_user_rel', column1='task_id', column2='user_id', string='Assignees', context={'active_test': False}, tracking=True)
    project_id = fields.Many2one('project.project', string='Project', recursive=True, compute='_compute_project_id', store=True, readonly=False, precompute=True, index=True, tracking=True,
                                 check_company=True, change_default=False, domain="_onchange_project_id")

    @api.onchange('project_id', 'user_ids')
    def _onchange_project_id(self):
        invited_partner_ids = self.project_id.message_partner_ids.ids
        return {'domain': {'user_ids': [('partner_id', 'in', invited_partner_ids)]}}

    @api.model
    def create(self, vals):
        return super(Task, self).create(vals)
