from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError


class ProjectProjectInherit(models.Model):
    _name = 'commercial.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit mail.thread and mail.activity.mixin

    project = fields.Char(tracking=True)  # Enable tracking to log changes in Chatter
    reference = fields.Char(tracking=True)
    client = fields.Many2one('res.partner', tracking=True)
    devis = fields.Binary(string="Devis", attachment=True)
    devis_filename = fields.Char("Filename")
    devis_url = fields.Char(help="URL for the quotation document", tracking=True)
    commercial = fields.Many2one('res.user', tracking=True)
    designer = fields.Many2one('res.users', racking=True)
    designer_assign_date = fields.Date(string='Designer Assign Date', tracking=True)
    bat = fields.Binary(string="BAT", attachment=True)
    bat_filename = fields.Char("Filename")
    description = fields.Text(string="Déscription")

    creation_date = fields.Date(default=fields.Date.context_today, tracking=True)
    comment = fields.Text(string="Commentaire")

    project_document = fields.Binary(attachment=True)
    project_document_filename = fields.Char("Filename")
    document_ids = fields.One2many('commercial.documents', 'project_id')
    product_ids = fields.One2many('commercial.products', 'project_id')

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

    @api.onchange('designer')
    def _onchange_designer(self):
        if self.designer:

            # Chatter message for designer assignment
            message = f"Le notification envoyer au designer {self.designer.name} avec succès"

            return {
                'warning': {
                    'title': 'Designer Assigné',
                    'message': message,
                }
            }
        else:
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

    def action_send_to_designer(self):
        # Ensure there's a designer assigned before proceeding
        if not self.designer:
            raise UserError("Aucun designer n'est attribué à ce projet.")

        # Create corresponding designer.project record
        designer_project_vals = {
            'reference_projet': self.id,  # Link to this commercial.project record
            'state_designer': 'draft',  # Initial state
            'commercial': self.env.user.id,  # Current user as commercial
        }

        # Create the designer project record
        designer_project = self.env['designer.name'].create(designer_project_vals)

        # Update the state_commercial to 'design_in_progress'
        self.write({
            'state_commercial': 'design_in_progress',
            'designer_assign_date': fields.Date.context_today(self),
        })

        # Send email notification to the designer
        template_id = self.env.ref('nn_majesty.email_template_designer_notification').id
        if template_id:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)

        # Log the action in the Chatter
        self.message_post(
            body=f"""Projet envoyé au designer:
             - État du projet changé à 'Design en cours'
             - Projet designer créé (ID: {designer_project.id})
             - Email de notification envoyé au designer"""
        )

        return True

    bat_cancel = fields.Boolean('BAT Annulé')
    is_favorite = fields.Boolean('Ajouter aux favoris')

    invalidation_reason = fields.Text(string="Raison de Refus BTA")

    def action_invalidate_designer(self):
        # Ensure there is a designer assigned
        if not self.designer:
            raise UserError("Aucun designer n'est attribué à ce projet.")
        else:
            self.bat_cancel = True
            self.state_commercial = 'design_in_progress'
        # Launch the wizard with project context
        return {
            'name': "Invalidate Designer",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.invalidate.designer',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_project_id': self.id},
        }

    def name_get(self):
        result = []
        for record in self:
            name = record.reference or 'New'
            result.append((record.id, name))
        return result
