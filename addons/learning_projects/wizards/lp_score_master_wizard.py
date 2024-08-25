from odoo import fields, models, api

SCORES = [
    ('0', 'Без оценки'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5')
]


class ScoreMasterWizard(models.TransientModel):
    _name = 'lp.score.master.wizard'
    _description = 'Description'

    author = fields.Many2one('res.partner', string="Автор", readonly=True)
    document_ids = fields.Many2many('ir.attachment', 'lp_score_master_wizard_ir_attachments_rel', 'wizard_id', 'attachment_id', string='Документы', readonly=True)

    score_master = fields.Selection(SCORES, string='Оценка от Магистра', tracking=True, required=True)

    @api.onchange('author')
    def load_documents(self):
        self.document_ids = self.author.document_ids

    def action_confirm(self):
        self.author.sudo().write({
            'score_master': self.score_master
        })

        return {'type': 'ir.actions.act_window_close'}
