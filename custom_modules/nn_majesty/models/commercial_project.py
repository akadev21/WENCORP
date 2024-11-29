from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectProjectInherit(models.Model):
    _name = 'commercial.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit mail.thread and mail.activity.mixin
    _rec_name = 'reference'  # Add this to make reference the default display field

    project = fields.Char(tracking=True)  # Enable tracking to log changes in Chatter
    reference = fields.Char(tracking=True)
    reference_devis = fields.Char(tracking=True)

    client = fields.Many2one('res.partner', tracking=True, default=lambda self: self.env.user.partner_id)
    devis = fields.Binary(string="Devis", attachment=True)
    devis_filename = fields.Char("Filename")
    devis_url = fields.Char(help="URL for the quotation document", tracking=True)
    commercial = fields.Many2one('res.user', tracking=True)
    designer = fields.Many2one('res.users', tracking=True)
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
    bat_cancel = fields.Boolean('BAT Annulé')
    bat_validated = fields.Boolean('BAT validée')
    is_favorite = fields.Boolean('Ajouter aux favoris')

    invalidation_reason = fields.Text(string="Raison de Refus BTA")

    state_commercial = fields.Selection(
        [
            ('preparation', 'Préparation'),
            ('design_in_progress', 'Design en cours'),
            ('design_in_review', 'Design en revue'),
            ('design_completed', 'Design terminé'),
            ('bc', 'BC'),
            ('bc_confirme', 'BC Confirmé'),
            ('BAT_in_progress', 'BAT Production en cours'),
            ('BAT_completed', 'BAT Production terminé'),
            ('production', 'Production')
        ],
        string='State',
        default='preparation',
        tracking=True  # Enable tracking for state changes
    )

    @api.model
    def create(self, values):
        # Get the sequence value (this includes the prefix and number)
        sequence = self.env['ir.sequence'].next_by_code('project.reference_fix_new')

        # Directly assign the sequence without zfill
        values['reference'] = sequence

        # Set creation date if not provided
        if 'creation_date' not in values:
            values['creation_date'] = fields.Date.context_today(self)

        # Create the record
        return super(ProjectProjectInherit, self).create(values)

    def action_send_to_designer(self):
        # Ensure there's a designer assigned before proceeding
        if not self.designer:
            raise UserError("Aucun designer n'est attribué à ce projet.")
            # Check if document_ids is empty
        if not self.document_ids:
            raise UserError("Aucun document n'est ajouté à ce projet.")

            # Check if product_ids is empty
        if not self.product_ids:
            raise UserError("Aucun produit n'est ajouté à ce projet.")

        # Create corresponding designer.project record
        designer_project_vals = {
            'reference_projet': self.id,  # Link to this commercial.project record
            'state_designer': 'draft',  # Initial state
            'commercial': self.env.user.id,  # Current user as commercial
            'client': self.client.id,
        }

        # Create the designer project record
        designer_project = self.env['designer.project'].create(designer_project_vals)

        # Copy product lines to designer project
        for product in self.product_ids:
            self.env['commercial.products'].create({
                'desginer_id': designer_project.id,
                'product_id': product.product_id.id,
                'quantity': product.quantity,
                'gender': product.gender,

                'quantity_delivered': product.quantity_delivered,
                'customizable': product.customizable,
                'description': product.description,
                'model_design': product.model_design,
                'model_design_filename': product.model_design_filename,
            })
        for documents in self.document_ids:
            self.env['commercial.documents'].create({
                'desginer_id': designer_project.id,
                'document_binary': documents.document_binary,
                'document_name': documents.document_name,
            })

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
             - Projet designer créé (ID: {self.designer})
             - {len(self.product_ids)} produits copiés vers le projet designer
             - Email de notification envoyé au designer"""
        )

        return True

    def action_invalidate_designer(self):
        self.bat_cancel = True
        designer_project = self.env['designer.project'].search([
            ('reference_projet', '=', self.id)
        ], limit=1)

        if designer_project:
            designer_project.write({'state_designer': 'design_not_validated'})

        return {
            'name': "Invalidate Designer",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.invalidate.designer',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_project_id': self.id},
        }

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Bon de Commande"
    )
    _sql_constraints = [
        ('unique_sale_order', 'unique(sale_order_id)', 'Each project can be linked to only one sale order!'),
        ('unique_project', 'unique(project_id)', 'Each sale order can only have one project!')
    ]

    # ... (other existing fields)

    def action_validate_design(self):
        """
        Create a sale order (BC) from the project information,
        and update project state to 'bc'
        """
        self.ensure_one()
        self.bat_cancel = False

        # Basic validation checks
        if not self.client:
            raise UserError("Veuillez sélectionner un client avant de créer le bon de commande.")

        if not self.reference:
            raise UserError("La référence du projet est obligatoire.")

        if self.sale_order_id:
            raise UserError("Un bon de commande existe déjà pour ce projet.")

        try:
            order_lines = []
            for product in self.product_ids:
                if not product.product_id:
                    continue

                order_line_vals = {
                    'product_id': product.product_id.id,
                    'product_uom_qty': product.quantity,
                    'qty_delivered': product.quantity_delivered,
                    'name': product.description or product.product_id.name,
                    'customizable': product.customizable,
                    'model_design': product.model_design,
                    'model_design_filename': product.model_design_filename,
                    'model_design_2_v': product.model_design_2_v,
                    'model_design_filename_2_v': product.model_design_filename_2_v,
                    'upload_bat_design': product.upload_bat_design,
                    'bat_design_name': product.bat_design_name,
                    # Add other relevant fields here
                }
                order_lines.append((0, 0, order_line_vals))

            # Prepare sale order data
            sale_order_vals = {
                'partner_id': self.client.id,
                'order_line': order_lines,
                'reference': self.reference,
                'bat': self.bat,
                'bat_filename': self.bat_filename,
                'state_commercial': self.state_commercial,
                'date_order': fields.Datetime.now(),
                'state': 'sale',
                'company_id': self.env.company.id,
            }

            # Set partner-specific fields
            if self.client.property_product_pricelist:
                sale_order_vals['pricelist_id'] = self.client.property_product_pricelist.id
            if self.client.property_payment_term_id:
                sale_order_vals['payment_term_id'] = self.client.property_payment_term_id.id
            if self.commercial:
                sale_order_vals['user_id'] = self.commercial.id

            # Create the sale order
            sale_order = self.env['sale.order'].sudo().create(sale_order_vals)

            # Update project state
            self.write({
                'state_commercial': 'bc',
                'sale_order_id': sale_order.id,
                'bat_validated': True,
            })

            # Find and update the related designer project
            designer_project = self.env['designer.project'].search([
                ('reference_projet', '=', self.id)
            ], limit=1)

            if designer_project:
                designer_project.write({'state_designer': 'design_validated'})

            # Log the creation in the chatter
            self.message_post(
                body=f"""Bon de commande créé avec succès:
                    - Numéro BC: {sale_order.name}
                    - Client: {self.client.name}
                    - État changé à 'BC'
                    - Projet designer mis à jour à 'Design validé'
                    - Date de création: {fields.Datetime.now()}""",
                message_type='notification'
            )

        except Exception as e:
            raise UserError(f"Erreur lors de la création du bon de commande: {str(e)}")

    def view_bc(self):
        """
        Open the corresponding 'Bon de Commande' form view for the related sale order.
        """
        self.ensure_one()  # Ensure the method is executed for a single record

        # Check if a related sale order exists
        if not self.sale_order_id:
            raise UserError("Aucun bon de commande lié trouvé pour cet enregistrement.")

        return {
            'name': 'Bon de Commande',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,  # Replace with the correct related sale.order field
            'view_mode': 'form',
            'target': 'current',
        }

    def action_review_design(self):
        """
        Send an email to the designer.
        """
        self.ensure_one()

        # Ensure that the designer is set
        if not self.designer:
            raise UserError("Le designer n'est pas défini pour ce projet.")

        # Retrieve the email template
        template = self.env.ref('nn_majesty.email_template_commercial_design_review', raise_if_not_found=False)

        # If the template exists, send the email
        if template:
            template.send_mail(self.id, force_send=True)
        else:
            raise UserError("Le modèle d'email de révision de design est introuvable.")

        # Optionally, you can log this action in the Chatter
        self.message_post(
            body=f"Le design a été envoyé pour révision au designer {self.designer.name}."
        )

        return True

    def action_send_to_usine(self):
        """
        Send the project to the usine (factory) and update the project state to 'production'.
        """
        self.ensure_one()

        # Ensure required fields are present
        if not self.client:
            raise UserError("Veuillez sélectionner un client pour ce projet.")

        if not self.product_ids:
            raise UserError("Aucun produit n'est associé à ce projet.")

        # Check if the current state allows sending to usine
        if self.state_commercial != 'bc':
            raise UserError("Le projet doit être en état 'BC' avant d'être envoyé à l'usine.")

        # Initialize variables and catch exceptions for robust error handling
        try:
            # Check if a project has already been sent to the usine
            existing_usine_project = self.env['usine.project'].search([('reference_projet', '=', self.id)], limit=1)
            if existing_usine_project:
                raise UserError(f"Ce projet a déjà été envoyé à l'usine (ID usine: {existing_usine_project.id}).")

            # Create usine project record
            usine_project_vals = {
                'reference_projet': self.id,  # Link to this commercial.project record
                'status_usin': 'attribuee',  # Initial state in usine
                'commercial': self.env.user.id,  # Current user as the commercial
            }
            usine_project = self.env['usine.project'].create(usine_project_vals)

            # Copy product lines to the usine project
            for product in self.product_ids:
                # Check if the product already exists in the usine project
                existing_usine_product = self.env['usine.products'].search([
                    ('usine_id', '=', usine_project.id),
                    ('product_id', '=', product.product_id.id),
                ], limit=1)

                if existing_usine_product:
                    # Update the quantity if the product already exists
                    existing_usine_product.quantity += product.quantity
                else:
                    # Create a new record for the product in the usine
                    self.env['usine.products'].create({
                        'usine_id': usine_project.id,
                        'product_id': product.product_id.id,
                        'quantity': product.quantity,
                        'gender': product.gender,
                        'usine': product.usine,
                        'quantity_delivered': product.quantity_delivered,
                        'customizable': product.customizable,
                        'description': product.description,
                        'model_design': product.model_design,
                        'model_design_filename': product.model_design_filename,
                        'model_design_2_v': product.model_design_2_v,
                        'model_design_filename_2_v': product.model_design_filename_2_v,
                        'upload_bat_design': product.upload_bat_design,
                        'bat_design_name': product.bat_design_name,

                    })

            # Update the project state to 'production'
            self.write({'state_commercial': 'production'})

            # Send email notification to the usine
            # Send email notification to the usine
            try:
                template = self.env.ref('nn_majesty.email_template_usine_notification', raise_if_not_found=False)
                if not template:
                    raise UserError(
                        "Le modèle d'email pour la notification à l'usine est introuvable. Veuillez le configurer.")
                template.send_mail(self.id, force_send=True)
            except Exception as email_error:
                raise UserError(f"Une erreur s'est produite lors de l'envoi de l'email : {email_error}")

            # Log the action in the Chatter
            self.message_post(
                body=f"""
                        Projet envoyé à l'usine :
                        - État du projet changé à 'Production'
                        - Projet usine créé (ID: {usine_project.id})
                        - {len(self.product_ids)} produits copiés vers le projet usine
                        - Email de notification envoyé à l'usine."""
            )

            # Return a success message or action
            return {
                'name': 'Usine Project',
                'type': 'ir.actions.act_window',
                'res_model': 'usine.project',
                'res_id': usine_project.id,
                'view_mode': 'form',
                'target': 'current',
            }

        except UserError as user_error:
            raise user_error  # Re-raise user errors for proper handling
        except Exception as e:
            raise UserError(f"Une erreur inattendue s'est produite : {str(e)}")

    def action_send_to_designer_BAT_request(self):
        """
        Envoie le projet au designer et demande le BAT Production
        si l'état est 'BC Confirmé'.
        """
        self.ensure_one()

        designer_project = self.env['designer.project'].search([
            ('reference_projet', '=', self.id)
        ], limit=1)

        if designer_project:
            designer_project.write({'state_designer': 'BAT_in_progress'})

        # Copier les lignes des produits

        self.write({
            'state_commercial': 'BAT_in_progress',
        })

        # Envoyer une notification par email au designer
        template_id = self.env.ref('nn_majesty.email_template_designer_notification_BAT_request').id
        if template_id:
            self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)

        # Log dans le chatter
        self.message_post(
            body=f"""
                Projet envoyé au designer pour BAT Production :
                - État changé à 'BAT Production en cours'
                - Projet designer créé (ID: {designer_project.id})
                - {len(self.product_ids)} produits copiés
                - Email de notification envoyé au designer ({self.designer.name}).
                """
        )

        return True
