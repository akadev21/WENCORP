from odoo import models, fields, api
from odoo.exceptions import UserError


class DesignerProject(models.Model):
    _name = 'designer.project'
    _description = 'Designer Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit mail.thread and mail.activity.mixin

    # Selection field to manage the state
    state_designer = fields.Selection(
        [
            ('draft', 'Draft'),
            ('control_in_progress', 'Control en cours'),
            ('design_validated', 'Design Validé'),
            ('design_not_validated', 'Non Validé')
        ],
        string='State',
        default='draft',
        tracking=True ) # This enables automatic tracking of state changes

    document_ids = fields.One2many('commercial.documents', 'desginer_id')
    product_ids = fields.One2many('commercial.products', 'desginer_id')
    reference_projet = fields.Many2one('commercial.project', string='Référence Projet')

    # Related fields from commercial.project
    designer = fields.Many2one(related='reference_projet.designer', string='Designer', readonly=True)
    designer_assign_date = fields.Date(related='reference_projet.designer_assign_date',
                                       string='Date d\'Attribution du Designer', readonly=True)

    description = fields.Text(related='reference_projet.description', string='Description', readonly=True)

    # Other fields
    commentaire = fields.Text(string="Commentaire")

    # Commercial field (get the user who created this record)
    commercial = fields.Many2one(
        'res.users',
        string='Commercial',
        default=lambda self: self.env.user,
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

    @api.model
    def create(self, vals):
        # Automatically set the commercial field to the current user on project creation
        if 'commercial' not in vals:
            vals['commercial'] = self.env.user.id
        return super(DesignerProject, self).create(vals)

    def action_send_design(self):
        """
        Action to send the design for review:
        - Validates BAT upload
        - Changes state to control_in_progress
        - Sends notification to commercial
        - Syncs products with commercial project
        """
        if not self.upload_bat:
            raise UserError("Veuillez télécharger le BAT avant d'envoyer le design.")

        # Update state to control_in_progress
        self.write({
            'state_designer': 'control_in_progress'
        })

        # Update related commercial project state if it exists
        if self.reference_projet:
            # First update the basic fields
            self.reference_projet.write({
                'state_commercial': 'design_completed',
                'bat': self.upload_bat,
                'bat_filename': self.bat_filename,
            })

            # Clear existing products in commercial project
            self.reference_projet.product_ids.unlink()

            # Create new product records for commercial project
            product_vals = []
            for product in self.product_ids:
                product_vals.append({
                    'project_id': self.reference_projet.id,
                    'product_id': product.product_id.id,
                    'quantity': product.quantity,
                    # Add any other fields you need to copy
                })

            # Create new product records
            if product_vals:
                self.env['commercial.products'].create(product_vals)

        # Send email notification to commercial
        template_id = self.env.ref('nn_majesty.email_template_commercial_design_review').id
        if template_id:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)

        # Log the action in the chatter with proper tracking
        self.message_post(
            body=f"""Design envoyé pour validation:
               - État changé à 'Control en cours'
               - BAT envoyé au commercial {self.commercial.name}
               - Produits synchronisés avec le projet commercial
               - Email de notification envoyé""",
            message_type='notification'
        )

        return True