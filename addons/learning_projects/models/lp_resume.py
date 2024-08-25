import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import config as odoo_conf

_logger = logging.getLogger(__name__)


class Resume(models.Model):
    _name = 'lp.resume'
    _inherit = ['mail.thread']
    _description = 'Резюме'

    author = fields.Many2one('res.partner', string="Автор", compute='_compute_author', readonly=True)
    name = fields.Char(related='author.name', string="ФИО", tracking=True, readonly=True)
    group = fields.Char(related='author.number_groups', string="Группа", tracking=True, readonly=True)
    short_description = fields.Html(string='О себе', sanitize_attributes=False, tracking=True)
    skills = fields.Many2many('res.partner.category', string='Навыки', tracking=True)
    areas_of_interest = fields.Many2many('lp.interest', string='Области интересов', tracking=True)

       
    def _compute_author(self):
        for rec in self:
            author = self.env['res.users'].browse(rec.create_uid.id).partner_id
            rec.author = author.id

    @api.model
    def create(self, vals):
        self.validate_count_creations()
        return super(Resume, self).create(vals)

    def validate_count_creations(self):
        resume = self.env['lp.resume'].search([('create_uid', '=', self.env.uid)])
        if len(resume) > int(odoo_conf['count_creation_resume']):
            raise ValidationError("Можно создать только 1 резюме")
