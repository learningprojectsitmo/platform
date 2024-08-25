import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_partner import now

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_group_external_ids(self):
        group_names = []
        for group in self.groups_id:
            group_names.append(group.name)
        return group_names

    def get_group_external_ids(self):
        group_names = []
        for group in self.groups_id:
            group_names.append(group.name)
        return group_names

    @api.model
    def create(self, values):
        # Call the original create method
        user = super(ResUsers, self).create(values)

        # Update related partners
        partners = self.env['res.partner'].sudo().search([('id', '=', user.partner_id.id)])
        v = {}
        group_external_ids = user.get_group_external_ids()

        if 'Admin' in group_external_ids:
            v['is_admin'] = True
        else:
            v['is_admin'] = False
        if 'Master' in group_external_ids:
            v['is_master'] = True
        else:
            v['is_master'] = False
        if 'Bachelor' in group_external_ids:
            v['is_bachelor'] = True
        else:
            v['is_bachelor'] = False

        if 'Lecturer' in group_external_ids:
            v['is_lecturer'] = True
        else:
            v['is_lecturer'] = False

        partners.sudo().write(v)

        return user

    def write(self, values):
        # Call the original write method
        res = super(ResUsers, self).write(values)

        # Update related partners
        for user in self:
            partners = self.env['res.partner'].sudo().search([('id', '=', user.partner_id.id)])
            v = {}
            group_external_ids = user.get_group_external_ids()
            if 'Admin' in group_external_ids:
                v['is_admin'] = True
            else:
                v['is_admin'] = False
            if 'Master' in group_external_ids:
                v['is_master'] = True
            else:
                v['is_master'] = False
            if 'Bachelor' in group_external_ids:
                v['is_bachelor'] = True
            else:
                v['is_bachelor'] = False

            if 'Lecturer' in group_external_ids:
                v['is_lecturer'] = True
            else:
                v['is_lecturer'] = False

            partners.sudo().write(v)

        return res

    def action_invite_user(self):
        """ create signup token for each user, and send their signup url by email """
        if self.env.context.get('install_mode', False):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            template = self.env.ref('auth_signup.mail_template_user_signup_account_created')
        assert template._name == 'mail.template'

        email_values = {
            'email_cc': False,
            'auto_delete': False,
            'message_type': 'user_notification',
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
        }

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            email_values['email_to'] = user.email
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                force_send = not (self.env.context.get('import_file', False))
                template.send_mail(user.id, force_send=force_send, raise_exception=True, email_values=email_values)
            _logger.info("Invite user email sent for user <%s> to <%s>", user.login, user.email)
