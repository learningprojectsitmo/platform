import logging
import base64
import zipfile
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
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
    group = fields.Char(string="Группа", tracking=True, readonly=True)
    short_description = fields.Html(string='О себе', sanitize_attributes=False)
    skills = fields.Many2many('res.partner.category', string='Навыки', tracking=True)
    areas_of_interest = fields.Many2many('lp.interest', string='Области интересов', tracking=True)

    check_box = fields.Boolean(string='Загрузить CV', default=False)
    file = fields.Binary(string='Name of field', attachment=True, index=True)

    @api.depends('author')
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

    @api.model
    def create_zip_archive(self, attachment_ids):
        # In-memory buffer to store the ZIP file
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for attachment_id in attachment_ids:
                _logger.info("for attachment %d", attachment_id['attachment_id'])
                attachment = self.env['ir.attachment'].browse(attachment_id['attachment_id'])
                name = attachment_id['name']
                if attachment:
                    # Decode the attachment's base64 data
                    data = base64.b64decode(attachment.datas)
                    # Add the file to the ZIP archive
                    zip_file.writestr(name + self._name.replace(".", "_"), data)

        # Prepare the ZIP file for downloading
        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()

        # Encode the ZIP file content so it can be stored in an ir.attachment
        zip_data = base64.b64encode(zip_content)

        # Create a new attachment for the ZIP file
        zip_attachment = self.env['ir.attachment'].create({
            'name': 'MassImportFiles_' + self._name.replace(".", "_") + '.zip',
            'type': 'binary',
            'datas': zip_data,
            'store_fname': 'Attachments.zip',
            'mimetype': 'application/zip',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{zip_attachment.id}?download=true',
            'target': 'new',
        }

    def mus_download_cv(self):
        attachment_ids = []
        for record in self:
            _logger.info("record %s", )
            record.generate_pdf()
            self.env.cr.execute("SELECT id FROM ir_attachment WHERE res_id = %s and res_model = 'lp.resume'", (record.id,))
            # Получаем результат запроса
            attachment_id = {}
            attachment = self.env.cr.fetchone()
            _logger.info("attachment %s", attachment)
            if attachment:
                attachment_id['name'] = record.name
                attachment_id['attachment_id'] = attachment[0]
                attachment_ids.append(attachment_id)
        _logger.info("Odoo version %s", attachment_ids)
        return self.create_zip_archive(attachment_ids)

    def generate_pdf(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        content = []

        # Загрузка шрифта, поддерживающего кириллицу
        pdfmetrics.registerFont(TTFont('Arial', '/mnt/extra-addons/learning_projects/static/src/Arial/arialmt.ttf'))  # Замените 'arial.ttf' на путь к вашему шрифту

        # Определение собственных стилей
        normal_style = ParagraphStyle(name='Normal', fontName='Arial')
        heading_style = ParagraphStyle(name='Heading2', fontName='Arial', fontSize=16, leading=20)

        # Добавляем информацию из резюме в документ
        if self.name:
            content.append(Paragraph(f"ФИО: {self.name}", normal_style))
        if self.group:
            content.append(Paragraph(f"Группа: {self.group}", normal_style))
        content.append(Paragraph("О себе:", heading_style))
        content.append(Paragraph(self.short_description, normal_style))
        content.append(Paragraph("Навыки:", heading_style))
        for skill in self.skills:
            content.append(Paragraph(skill.name, normal_style))
        content.append(Paragraph("Области интересов:", heading_style))
        for interest in self.areas_of_interest:
            content.append(Paragraph(interest.name, normal_style))

        doc.build(content)

        # Сохраняем PDF в поле 'file'
        pdf_content = buffer.getvalue()
        self.file = base64.b64encode(pdf_content).decode('utf-8')
        buffer.close()
