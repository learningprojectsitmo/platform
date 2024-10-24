from odoo import fields, models, api
# from .utils import generate_technical_specification_pdf

from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO
import base64

STATUS = [
    ('UnApproval', 'Не утверждено'),
    ('Approval', 'Утверждено'),
]


class TechnicalSpecification(models.Model):
    _name = 'lp.technical.specification'
    _inherit = ['mail.thread']
    _description = 'Technical Specification'


    # todo in ui (xml) required=True хз, тут надо думать
    # todo status approved by lector
    name = fields.Char(string='Название проекта*', required=True)
    target = fields.Text(string='Цель*' ) #required=True

    status = fields.Selection(STATUS, string='Статус', readonly=True, tracking=True, default='UnApproval')
    message_partner_ids = fields.Many2many('res.partner', string='Message Partners')

    # Сроки выполнения
    date_start = fields.Date(string='Начало')
    date_end = fields.Date(string='Конец')

    # Исполнитель проекта (руководитель проекта)
    author = fields.Many2one('res.partner', string='Автор*', readonly=True, tracking=True)

    # Термины и сокращения
    terms_ids = fields.Many2many('lp.terms', string='Термины и сокращения*' ) #required=True

    # Технические требования
    specification_ids = fields.Many2many('lp.specification', string='Техническое требование*' ) #required=True

    # Содержание работы (этапы по срокам, можно в таблицу)
    # этапы
    task_stage_ids = fields.Many2many('lp.stages', string='Этапы задач')
    # задачи
    task_task_ids = fields.Many2many('lp.task', string='Задачи')

    # Основные результаты работы и формы их представления
    results = fields.Text(string='Основные результаты работы', help="Основные результаты работы и формы их представления*") # required=True

    file = fields.Binary(string='Name of field', attachment=True, index=True)

    def create_project(self):
        params = self.env['ir.config_parameter'].sudo()
        project_stage_2_id = int(params.get_param('project_stage_2_id'))
        type_ids = []

        for lp_stages in self.task_stage_ids:
            type_id = self.env['project.task.stage'].sudo().create({'name': lp_stages.name, 'sequence': lp_stages.sequence})
            type_ids.append(type_id)

        project = self.env['project.project'].sudo().create({
            'name': self.name,
            'stage_id': project_stage_2_id,
            'type_ids': type_ids,
        })
        project.sudo().write({'message_partner_ids': [(4, self.author.id)]})

        # project.write({'project': project.id, 'status': 'OnApprovalTex'})
        # self.env['project.task'].create({'name': self.name})

    def generate_technical_specification_pdf(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2 * cm, rightMargin=cm, topMargin=cm, bottomMargin=cm)
        content = []

        style = [
            ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
            ('FONT', (0, 0), (-1, -1), 'times'),
            ('SIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('WORDWRAP', (0, 0), (-1, -1)),
        ]

        # Load font supporting Cyrillic characters
        pdfmetrics.registerFont(TTFont('times', '/mnt/extra-addons/learning_projects/static/src/times.ttf'))

        # Define custom styles
        normal_style = ParagraphStyle(name='Normal', fontName='times', fontSize=14, leading=18, spaceBefore=0)
        heading_style = ParagraphStyle(name='Heading2', fontName='times', fontSize=14, leading=20, spaceBefore=12, leftIndent=12)

        # Add information from the Technical Specification to the document
        if self.name:
            content.append(Paragraph("1. Название проекта:", heading_style))
            content.append(Paragraph(self.name, normal_style))
        if self.target:
            content.append(Paragraph("2. Цель (назначение):", heading_style))
            content.append(Paragraph(self.target, normal_style))
        if self.date_start and self.date_end:
            content.append(Paragraph(f"3. Сроки выполнения:", heading_style))
            content.append(Paragraph(f" Начало - {self.date_start}, Конец - {self.date_end}", normal_style))
        if self.author:
            content.append(Paragraph("4. Исполнитель проекта (руководитель проекта):", heading_style))
            content.append(Paragraph(self.author.name, normal_style))
        if self.terms_ids:
            content.append(Paragraph("5. Термины и сокращения:", heading_style))
            for term in self.terms_ids:
                content.append(Paragraph(f"{term.name} - {term.description}", normal_style))
        if self.specification_ids:
            content.append(Paragraph("6. Технические требования (технические, дидактические, программные, эргономические, экологические и др.)", heading_style))
            spec_table_data = [['Наименование', 'База данных', 'Заказчики']]
            for spec in self.specification_ids:
                spec_table_data.append([spec.name, spec.data_base, spec.customers])

            # Calculate column widths based on content length
            col_widths = [max(len(str(cell)) * 6 for cell in column) for column in zip(*spec_table_data)]

            # Adjust column widths to fit within the page
            total_width = sum(col_widths)
            if total_width > A4[0] - doc.leftMargin - doc.rightMargin:
                scaling_factor = (A4[0] - doc.leftMargin - doc.rightMargin) / total_width
                col_widths = [width * scaling_factor for width in col_widths]
            # colWidths = col_widths,
            spec_table = Table(spec_table_data, style=style, )
            content.append(spec_table)

        if self.task_stage_ids:
            content.append(Paragraph("7. Содержание работы (этапы по срокам, можно в таблицу)", heading_style))
            content.append(Paragraph("Таблица 1 - Этапы задач проекта", heading_style))
            stage_table_data = [['Этапы задач']]
            for stage in self.task_stage_ids:
                stage_table_data.append([stage.name])
            max_widths = [max(len(str(cell)) for cell in column) * 10 for column in zip(*stage_table_data)]
            stage_table = Table(stage_table_data, colWidths=max_widths, style=[('GRID', (0, 0), (-1, -1), 1, (0, 0, 0))])
            stage_table.setStyle(style)

            content.append(stage_table)
            content.append(Paragraph("\n           \n", heading_style))
        if self.task_task_ids:
            content.append(Paragraph("Таблица 2 - Задачи", heading_style))
            task_table_data = [['Задачи', 'Описание', 'Ответственный']]
            for task in self.task_task_ids:
                task_table_data.append([task.name, task.description, task.assignees.display_name])
            max_widths = [max(len(str(cell)) for cell in column) * 10 for column in zip(*task_table_data)]
            task_table = Table(task_table_data, colWidths=max_widths, style=[('GRID', (0, 0), (-1, -1), 1, (0, 0, 0))])
            task_table.setStyle(style)
            content.append(task_table)
        if self.results:
            content.append(Paragraph("8. Основные результаты работы: ", heading_style))
            content.append(Paragraph(self.results, normal_style))

        doc.build(content)

        # Save PDF to the 'file' field
        pdf_content = buffer.getvalue()
        self.file = base64.b64encode(pdf_content).decode('utf-8')
        buffer.close()

    def generate_pdf(self):
        self.generate_technical_specification_pdf()
