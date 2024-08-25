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


from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO
import base64


def generate_technical_specification_pdf(self):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    content = []

    # Load font supporting Cyrillic characters
    pdfmetrics.registerFont(TTFont('Arial', '/mnt/extra-addons/learning_projects/static/src/Arial/arialmt.ttf'))

    # Define custom styles
    normal_style = ParagraphStyle(name='Normal', fontName='Arial')
    heading_style = ParagraphStyle(name='Heading2', fontName='Arial', fontSize=16, leading=20)

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
        spec_table = Table(spec_table_data, style=[('GRID', (0, 0), (-1, -1), 1, (0, 0, 0))])
        spec_table.setStyle([('FONT', (0, 0), (-1, -1), 'Arial'),
                             ('SIZE', (0, 0), (-1, -1), 10),
                             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                             ('ALIGN', (0, 0), (-1, -1), 'LEFT')])
        content.append(spec_table)

    if self.task_stage_ids:
        content.append(Paragraph("7. Содержание работы (этапы по срокам, можно в таблицу)", heading_style))
        stage_table_data = [['Этапы задач']]
        for stage in self.task_stage_ids:
            stage_table_data.append([stage.name])
        stage_table = Table(stage_table_data, colWidths=[500], style=[('GRID', (0, 0), (-1, -1), 1, (0, 0, 0))])
        stage_table.setStyle([('FONT', (0, 0), (-1, -1), 'Arial'),
                              ('SIZE', (0, 0), (-1, -1), 10),
                              ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                              ('ALIGN', (0, 0), (-1, -1), 'LEFT')])
        content.append(stage_table)
        content.append(Paragraph("\n           \n", heading_style))
    if self.task_task_ids:
        task_table_data = [['Задачи', 'Описание', 'Ответственный']]
        for task in self.task_task_ids:
            task_table_data.append([task.name, task.description, task.assignees.display_name])
        task_table = Table(task_table_data, colWidths=[200], style=[('GRID', (0, 0), (-1, -1), 1, (0, 0, 0))])
        task_table.setStyle([('FONT', (0, 0), (-1, -1), 'Arial'),
                             ('SIZE', (0, 0), (-1, -1), 10),
                             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                             ('ALIGN', (0, 0), (-1, -1), 'LEFT')])
        content.append(task_table)
    if self.results:
        content.append(Paragraph("8. Основные результаты работы: ", heading_style))
        content.append(Paragraph(self.results, normal_style))

    doc.build(content)

    # Save PDF to the 'file' field
    pdf_content = buffer.getvalue()
    self.file = base64.b64encode(pdf_content).decode('utf-8')
    buffer.close()
