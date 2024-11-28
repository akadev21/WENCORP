from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DesignerProject(models.Model):
    _name = 'designer.project'
    _description = 'Designer Project'
    # Inherit mail.thread and mail.activity.mixin
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'  # Add this to make reference the default display field

    # Selection field to manage the state
    state_designer = fields.Selection(
        [
            ('draft', 'Draft'),
            ('control_in_progress', 'Control en cours'),
            ('design_validated', 'Design Validé'),
            ('design_not_validated', 'Non Validé'),
            ('BAT_in_progress', 'BAT Production en cours'),
            ('BAT_completed', 'BAT Production terminé'),
        ],
        # compute='_compute_bat_cancel',
        string='State',
        default='draft',
        tracking=True)  # This enables automatic tracking of state changes

    document_ids = fields.One2many('commercial.documents', 'desginer_id')
    product_ids = fields.One2many('commercial.products', 'desginer_id')
    reference_projet = fields.Many2one(
        'commercial.project', string='Référence Projet')
    is_favorite = fields.Boolean(
        string="Is Favorite",
        related='reference_projet.is_favorite',
        readonly=False,  # Set to False if you want users to edit the value
        store=True  # Optional: Store the value in the database for faster access
    )
    # Related fields from commercial.project
    designer = fields.Many2one(
        related='reference_projet.designer', string='Designer', readonly=True)
    designer_assign_date = fields.Date(related='reference_projet.designer_assign_date',
                                       string='Date d\'Attribution du Designer', readonly=True)

    description = fields.Text(
        related='reference_projet.description', string='Description')

    # Other fields
    commentaire = fields.Text(string="Commentaire")

    # Commercial field (get the user who created this record)
    commercial = fields.Many2one(
        'res.users',
        string='Commercial',
        default=lambda self: self.env.user,
        readonly=True
    )
    client = fields.Many2one(
        'res.partner',
        string='Client',
        default=lambda self: self.env.user.partner_id,
        readonly=True
    )

    # Binary field to upload BAT
    upload_bat = fields.Binary(string="Upload BAT", attachment=True)
    bat_filename = fields.Char(string="BAT Filename")

    project_document = fields.Binary(
        related='reference_projet.project_document',
        string="Project Document",
        readonly=True
    )

    project_document_filename = fields.Char(
        related='reference_projet.project_document_filename',
        string="Project Document Filename",
        readonly=True
    )
    reference = fields.Char(
        related='reference_projet.reference',
        string="Référence",
        readonly=True
    )
    bat_cancel = fields.Boolean(
        related='reference_projet.bat_cancel',
        string="bat_cancel",
        readonly=True
    )
    bat_validated = fields.Boolean(
        related='reference_projet.bat_validated',
        string="bat_validated",
        readonly=True
    )
    invalidation_reason = fields.Text(
        related='reference_projet.invalidation_reason',
        string="Raison de Refus BTA",
        readonly=True
    )
    comment = fields.Text(
        string="Commentaire",
    )
    upload_bat_design = fields.Binary(string="Upload BAT", attachment=True)
    bat_design_name = fields.Char(required=True)

    @api.model
    def create(self, vals):
        # Automatically set the commercial field to the current user on project creation
        if 'commercial' not in vals:
            vals['commercial'] = self.env.user.id
        return super(DesignerProject, self).create(vals)

    def action_send_design(self):

        # Ensure BAT is uploaded
        if not self.upload_bat:
            raise UserError("Veuillez télécharger le BAT avant d'envoyer le design.")

        # Log current state for debugging
        _logger.info(f"Initial state_designer: {self.state_designer}")

        # Update state to 'control_in_progress'
        try:
            self.write({'state_designer': 'control_in_progress'})
            print("++++++++++++++++++++++++++++", self.state_designer)
            _logger.info(f"Updated state_designer: {self.state_designer}")
        except Exception as e:
            _logger.error(f"Failed to update state_designer: {str(e)}")
            raise UserError(f"Erreur lors de la mise à jour de l'état : {str(e)}")

        # If a commercial project reference exists, sync data
        if self.reference_projet:
            try:
                # Update commercial project basic fields
                self.reference_projet.write({
                    'state_commercial': 'design_completed',
                    'bat': self.upload_bat,
                    'bat_filename': self.bat_filename,
                    'comment': self.comment,
                })

                # Clear existing products in the commercial project
                self.reference_projet.product_ids.unlink()

                # Create new product records in the commercial project
                product_vals = [{
                    'project_id': self.reference_projet.id,
                    'product_id': product.product_id.id,
                    'quantity': product.quantity,
                    'gender': product.gender,
                    'customizable': product.customizable,
                    'description': product.description,
                    'model_design': product.model_design,
                    'model_design_2_v': product.model_design_2_v,
                    'model_design_filename_2_v': product.model_design_filename_2_v,
                    'upload_bat_design': product.upload_bat_design,
                    'usine': product.usine.id,

                    'model_design_filename': product.model_design_filename,
                } for product in self.product_ids]

                if product_vals:
                    self.env['commercial.products'].create(product_vals)

                # Clear existing documents in the commercial project
                self.reference_projet.document_ids.unlink()

                # Create new document records in the commercial project
                document_vals = [{
                    'project_id': self.reference_projet.id,
                    'document_binary': document.document_binary,
                    'document_name': document.document_name,
                } for document in self.document_ids]

                if document_vals:
                    self.env['commercial.documents'].create(document_vals)

            except Exception as e:
                _logger.error(f"Failed to sync with commercial project: {str(e)}")
                raise UserError(f"Erreur lors de la synchronisation avec le projet commercial : {str(e)}")

        # Send email notification to commercial
        try:
            template_id = self.env.ref('nn_majesty.email_template_commercial_design_review').id
            if template_id:
                self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
                _logger.info("Email notification sent successfully.")
        except Exception as e:
            _logger.error(f"Failed to send email notification: {str(e)}")
            raise UserError(f"Erreur lors de l'envoi de l'email : {str(e)}")

        # Log the action in the chatter
        commercial_ref = self.reference_projet.reference if self.reference_projet else "Unknown"
        print("++++++++++++++++++++++++++++", self.state_designer)
        self.message_post(
            body=f"""Design envoyé pour validation :
                - État changé à 'Control en cours'
                - BAT envoyé au commercial {self.commercial.name}
                - Projet commercial mis à jour (Réf: {commercial_ref})
                - {len(self.product_ids)} produits synchronisés avec le projet commercial
                - {len(self.document_ids)} documents synchronisés avec le projet commercial
                - Email de notification envoyé""",
            message_type='notification'
        )

        return True

    def send_pdf_bat(self):
        for record in self:
            try:
                record.write({'state_designer': 'BAT_completed'})
                _logger.info(f"Updated state_designer to 'BAT_completed' for record ID: {record.id}")
            except Exception as e:
                _logger.error(f"Failed to update state_designer: {str(e)}")
                raise UserError(f"Erreur lors de la mise à jour de l'état : {str(e)}")

            # Ensure that reference_projet is properly set on the commercial project
            commercial_project = self.env['commercial.project'].search([
                ('reference_projet', '=', record.id)
            ], limit=1)

            if commercial_project:
                commercial_project.write({'state_commercial': 'BAT_completed'})
                _logger.info(
                    f"Updated state_commercial to 'BAT_completed' for commercial project ID: {commercial_project.id}")
            else:
                _logger.error(f"No commercial project found for designer project ID: {record.id}")
                raise UserError("No commercial project found linked to this designer project.")

            # Send email notification to the commercial
            try:
                template_id = self.env.ref('nn_majesty.email_template_commercial_design_review_bat_pfd',
                                           raise_if_not_found=False)
                if not template_id:
                    _logger.error(
                        "Email template not found: 'nn_majesty.email_template_commercial_design_review_bat_pfd'.")
                    raise UserError("Le modèle d'email est introuvable. Veuillez vérifier sa configuration.")

                # Send the email
                template_id.send_mail(record.id, force_send=True)
                _logger.info(f"Email notification sent successfully for record ID: {record.id}")
            except Exception as e:
                _logger.error(f"Failed to send email notification: {str(e)}")
                raise UserError(f"Erreur lors de l'envoi de l'email : {str(e)}")

            # Log the action in the chatter
            commercial_ref = record.reference_projet.reference if record.reference_projet else "Unknown"
            record.message_post(
                body=f"""Design BAT PDF envoyé pour validation :
                    - État changé à 'BAT Production terminé'
                    - BAT Design validé pour le projet (Réf: {commercial_ref})
                    - Email de notification envoyé à {record.commercial.name if record.commercial else "commercial inconnu"}""",
                message_type='notification'
            )

        return True
