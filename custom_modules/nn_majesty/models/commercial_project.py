from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError


class ProjectProjectInherit(models.Model):
    _name = 'commercial.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit mail.thread and mail.activity.mixin
    _rec_name = 'reference'  # Add this to make reference the default display field

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
            ('production', 'Production')
        ],
        string='State',
        default='preparation',
        tracking=True  # Enable tracking for state changes
    )

    # @api.onchange('designer')
    # def _onchange_designer(self):
    #     if self.designer:
    #
    #         # Chatter message for designer assignment
    #         message = f"Le notification envoyer au designer {self.designer.name} avec succès"
    #
    #         return {
    #             'warning': {
    #                 'title': 'Designer Assigné',
    #                 'message': message,
    #             }
    #         }
    #     else:
    #         self.designer_assign_date = False
    #         return {}

    @api.model
    def create(self, values):
        # Get the sequence value (this includes the prefix and number)
        sequence = self.env['ir.sequence'].next_by_code('project.reference_fix_new') or 'PRO-0001'

        # Directly assign the sequence without zfill
        values['reference'] = sequence

        # Set creation date if not provided
        if 'creation_date' not in values:
            values['creation_date'] = fields.Date.context_today(self)

        # Assign designer date if a designer is set
        if 'designer' in values and values['designer']:
            values['designer_assign_date'] = fields.Date.context_today(self)

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
            'commercial': self.env.user.id,
            'client': self.env.user.id,  # Current user as commercial
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
                'usine': product.usine,
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
        # Ensure there is a designer assigned
        if not self.designer:
            raise UserError("Aucun designer n'est attribué à ce projet.")
        else:
            self.bat_cancel = True
            self.state_commercial = 'design_in_progress'
        _logger.info("Attempting to update state_commercial to 'design_in_review'")
        self.write({'state_commercial': 'design_in_review'})
        _logger.info("State update executed")

        # Launch the wizard with project context
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
                    'name': product.description or product.product_id.name,
                    'gender': product.gender,
                    'customizable': product.customizable,
                    'quantity_delivered': product.quantity_delivered,
                    'model_design': product.model_design,
                    'usine': product.usine,
                    'model_design_filename': product.model_design_filename,

                }
                order_lines.append((0, 0, order_line_vals))
            # Prepare sale order data - note the commercial field is res.users
            sale_order_vals = {
                'partner_id': self.client.id,
                'order_line': order_lines,
                'reference': self.reference,
                'date_order': fields.Datetime.now(),
                'state': 'sale',
                'company_id': self.env.company.id,
            }

            # Get partner's pricelist if it exists
            if self.client.property_product_pricelist:
                sale_order_vals['pricelist_id'] = self.client.property_product_pricelist.id

            # Get partner's payment terms if they exist
            if self.client.property_payment_term_id:
                sale_order_vals['payment_term_id'] = self.client.property_payment_term_id.id

            # If commercial exists, set as salesperson
            if self.commercial:
                sale_order_vals['user_id'] = self.commercial.id

            # Create the sale order
            sale_order = self.env['sale.order'].sudo().create(sale_order_vals)

            # First, change state to 'bc'
            self.write({
                'state_commercial': 'bc',
                'sale_order_id': sale_order.id
            })
            self.bat_validated = True
            # Log the creation in the chatter
            self.message_post(
                body=f"""Bon de commande créé avec succès:
                    - Numéro BC: {sale_order.name}
                    - Client: {self.client.name}
                    - État changé à 'BC'
                    - Date de création: {fields.Datetime.now()}""",
                message_type='notification'
            )

            # Return action to open the created sale order
            return {
                'name': 'Bon de Commande',
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': sale_order.id,
                'view_mode': 'form',
                'target': 'current',
            }

        except Exception as e:
            raise UserError(f"Erreur lors de la création du bon de commande: {str(e)}")

    def action_review_design(self):
        """
        Send an email to the designer and update the associated project state to 'design_in_review'.
        """
        self.ensure_one()

        # Ensure a designer is assigned
        if not self.designer:
            raise UserError("Aucun designer n'est attribué à ce projet.")

        # Ensure the designer project exists
        designer_project = self.env['designer.project'].search([('reference_projet', '=', self.id)], limit=1)
        if not designer_project:
            raise UserError("Aucun projet associé trouvé pour le designer.")

        try:
            # Update the state of the designer project
            designer_project.write({'state_designer': 'design_not_validated'})

            # Update the state of the commercial project
            self.write({'state_commercial': 'design_in_review'})

            # Send email notification to the designer
            template_id = self.env.ref('nn_majesty.email_template_design_review').id
            if template_id:
                self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)

            # Log the action in the Chatter
            self.message_post(
                body=f"""
                Le design a été envoyé pour révision:
                - État du projet commercial mis à jour à 'Design en revue'
                - État du projet designer mis à jour à 'In Review'
                - Notification par email envoyée au designer ({self.designer.name}).
                """
            )

            return True

        except Exception as e:
            raise UserError(f"Une erreur s'est produite lors de l'envoi pour révision: {str(e)}")

    def action_send_to_usine(self):
        """
        Send the project to the usine (factory) and update project state to 'production'.
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

        try:
            # Create usine project record
            usine_project_vals = {
                'reference_projet': self.id,  # Link to this commercial.project record
                'state_usine': 'draft',  # Initial state in usine
                'commercial': self.env.user.id,  # Current user as the commercial
            }
            usine_project = self.env['usine.project'].create(usine_project_vals)

            # Copy product lines to the usine project
            for product in self.product_ids:
                self.env['usine.products'].create({
                    'usine_id': usine_project.id,
                    'product_id': product.product_id.id,
                    'quantity': product.quantity,
                    'gender': product.gender,
                    'usine' : product.usine,
                    'quantity_delivered': product.quantity_delivered,
                    'customizable': product.customizable,
                    'description': product.description,
                    'model_design': product.model_design,
                    'model_design_filename': product.model_design_filename,
                })

            # Update the project state to 'production'
            self.write({
                'state_commercial': 'production',
            })

            # Send email notification to the usine
            template_id = self.env.ref('nn_majesty.email_template_usine_notification').id
            if template_id:
                self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)

            # Log the action in the Chatter
            self.message_post(
                body=f"""Projet envoyé à l'usine:
                 - État du projet changé à 'Production'
                 - Projet usine créé (ID: {usine_project.id})
                 - {len(self.product_ids)} produits copiés vers le projet usine
                 - Email de notification envoyé à l'usine."""
            )

            return True

        except Exception as e:
            raise UserError(f"Une erreur s'est produite lors de l'envoi à l'usine: {str(e)}")
