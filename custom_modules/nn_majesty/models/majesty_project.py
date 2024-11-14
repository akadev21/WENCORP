from odoo import models, fields, api
from datetime import datetime


class ProjectProjectInherit(models.Model):
    _name = 'majesty.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit mail.thread and mail.activity.mixin

    name = fields.Char(string='Projet', tracking=True)  # Enable tracking to log changes in Chatter
    reference = fields.Char(string='Reference', tracking=True)
    client_id = fields.Many2one('res.partner', string='Client', tracking=True)
    designer = fields.Many2one('res.users', string='Designer', tracking=True)
    creation_date = fields.Date(string='Creation Date', default=fields.Date.context_today, tracking=True)
    designer_assign_date = fields.Date(string='Designer Assign Date', tracking=True)
    description = fields.Text(string="Description")
    comment = fields.Text(string="Commentaire")
    ref_devis = fields.Binary(string="Reference Devis", attachment=True)
    ref_devis_filename = fields.Char("Filename")
    bat = fields.Binary(string="BAT", attachment=True)
    bat_filename = fields.Char("Filename")
    project_document = fields.Binary(string="Document Projets", attachment=True)
    project_document_filename = fields.Char("Filename")
    document_ids = fields.One2many('majesty.documents', 'project_id', string='Documents')
    product_ids = fields.One2many('majesty.products', 'project_id', string='Majesty Products')
    devis_url = fields.Char(string='Devis URL', help="URL for the quotation document", tracking=True)

    state_commercial = fields.Selection(
        [
            ('preparation', 'Préparation'),
            ('design_in_progress', 'Design en cours'),
            ('design_completed', 'Design terminé'),
            ('bc', 'BC')
        ],
        string='State',
        default='preparation',
        tracking=True  # Enable tracking for state changes
    )
    state_designer = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('control_in_progress', 'Contrôle en cours'),
            ('control_validated', 'Validé'),
            ('control_not_validated', 'Non validé')
        ],
        string='État',  # French translation for "State"
        default='draft',
        tracking=True  # Enable tracking for state changes
    )

    @api.onchange('designer')
    def _onchange_designer(self):
        if self.designer:
            self.state_commercial = 'design_in_progress'
            self.designer_assign_date = fields.Date.context_today(self)

            # Chatter message for designer assignment
            message = f"Attribution : le {self.designer_assign_date} - Designer : {self.designer.name}"
            return {
                'warning': {
                    'title': 'Designer Assigned',
                    'message': message,
                }
            }
        else:
            self.state_commercial = 'preparation'
            self.designer_assign_date = False
            return {}

    @api.model
    def create(self, values):
        sequence = self.env['ir.sequence'].next_by_code('project.reference_fix_new') or '0001'
        reference = sequence.zfill(4)

        values['reference'] = reference
        if 'creation_date' not in values:
            values['creation_date'] = fields.Date.context_today(self)

        if 'designer' in values and values['designer']:
            values['designer_assign_date'] = fields.Date.context_today(self)

        return super(ProjectProjectInherit, self).create(values)
