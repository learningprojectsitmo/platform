from odoo import fields, models, api

SCORES = [
    ('0', 'Без оценки'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5')
]


class LoadDocumentWizard(models.TransientModel):
    _name = 'lp.load.document.wizard'
    _description = 'Description'

    partner_id = fields.Many2one('res.partner', 'Customer', default=lambda self: self.env.user.partner_id, required=True, readonly=True)
    document_ids = fields.Many2many('ir.attachment', 'lp_load_document_wizard_ir_attachments_rel', 'wizard_id', 'attachment_id', string='Документы')

    @api.onchange('partner_id')
    def load_documents(self):
        self.document_ids = self.partner_id.document_ids

    def action_confirm(self):
        self.ensure_one()

        attachments = self.env['ir.attachment'].sudo().search([('id', '=', self.document_ids.id)])
        attachments.sudo().write({'res_model': 'res.partner',
                                  'public': True})

        self.partner_id.sudo().write({
            'document_ids': self.document_ids
        })

        return {'type': 'ir.actions.act_window_close'}
