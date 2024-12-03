from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one(
        'commercial.project',
        string="Projet Commercial",
        ondelete='cascade'
    )
    reference = fields.Char(
        string='Référence',
        tracking=True,
        help="Référence unique pour ce bon de commande"
    )
    active = fields.Boolean(default=True)

    bat = fields.Binary(
        string="BAT",
        readonly=True
    )
    bat_filename = fields.Char(
        string="Nom du fichier",
        readonly=True
    )

    state_commercial = fields.Selection(
        related="project_id.state_commercial",
        string="État Commercial",
        readonly=True
    )

    @api.model
    def action_confirm_bc(self):
        for order in self:
            try:
                # Initialize the project update data
                project_updates = {
                    'state_commercial': 'bc_confirme',
                }

                # Prepare a string to collect information for each order line, including size and quantity_size
                line_details = []

                for line in order.order_line:
                    # Get the quantity, quantity_size, and related sizes from the order line
                    quantity = line.product_uom_qty
                    quantity_size = line.quantity_size if hasattr(line,
                                                                  'quantity_size') else 0  # Ensure quantity_size exists
                    size_info = ", ".join([size.name for size in line.size_ids])  # Collecting size names from size_ids

                    # Collect size values for each line
                    detail_line_value = {
                        'size': size_info,  # Collecting size names as a string (or list of sizes if needed)
                        'quantity': quantity,
                        'quantity_size': quantity_size
                    }

                    # Add the line and size information to the project update
                    project_updates['quantity'] = quantity

                    # Append order line details, including size and quantity_size
                    line_details.append(
                        f"- Ligne {line.product_id.name}: Quantité: {quantity}, Quantité Taille: {quantity_size}, Tailles: {size_info if size_info else 'Non spécifié'}"
                    )

                    # Optionally, log the `detail_line_value` if needed for debugging
                    _logger.info(f"Detail for order line {line.product_id.name}: {detail_line_value}")

                # Update the project with the new information
                order.project_id.write(project_updates)

                # Prepare message to send in the project Chatter with line and size details
                order.project_id.message_post(
                    body=f"""Bon de commande confirmé :
                           - État mis à jour : 'BC Confirmé'
                           - Référence : {order.reference}
                           - Fichier BAT : {order.bat_filename or 'Non spécifié'}
                           - Détails des lignes de commande:
                           {chr(10).join(line_details)}""",
                    message_type='notification'
                )

                # Optionally log in the Sale Order Chatter with line and size details
                order.message_post(
                    body=f"Bon de commande confirmé. Projet lié mis à jour ({order.project_id.reference}). Détails des lignes de commande: {chr(10).join(line_details)}"
                )

            except UserError as ue:
                _logger.error(f"Erreur utilisateur lors de la confirmation du BC: {str(ue)}")
                raise ue
            except Exception as e:
                _logger.error(f"Erreur lors de la confirmation du BC: {str(e)}")
                raise UserError(
                    f"Une erreur inattendue s'est produite lors de la confirmation du bon de commande: {str(e)}")


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    # Champs personnalisés pour les détails du produit
    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('unisex', 'H/F')
    ], string='Sexe')

    customizable = fields.Boolean(string='Personnalisable')

    usine = fields.Many2one(
        'res.users',
        string='Usine',
        tracking=True
    )

    description = fields.Text(
        string="Description de l'article",
        help="Description spécifique à la ligne de commande"
    )

    quantity = fields.Float(
        string="Quantité prévue",
        related='product_uom_qty',
        readonly=False
    )

    quantity_delivered = fields.Float(
        string="Quantité livrée",
        related='qty_delivered',
        readonly=False
    )

    # Champs pour les designs de modèle
    model_design = fields.Binary(
        string="Modèle design (Vue de face)",
        attachment=True,
        help="Fichier de conception du modèle - vue de face"
    )
    model_design_filename = fields.Char(string="Nom du fichier BAT (Vue de face)")

    model_design_2_v = fields.Binary(
        string="Modèle design (Vue de dos)",
        attachment=True,
        help="Fichier de conception du modèle - vue de dos"
    )
    model_design_filename_2_v = fields.Char(string="Nom du fichier BAT (Vue de dos)")
    client_customization = fields.Text(string="Client Customization Details",
                                       help="Detailed customization information for this order line")
    size_ids = fields.One2many(
        'sale.order.line.size',
        'line_id',  # Matches the Many2one field in sale.order.line.size
        string="Sizes and Quantities"
    )

    def open_line_details(self):
        """
        Opens the 'sale.order.line.size' details related to this sale order line.
        """
        self.ensure_one()  # Ensure that the action is triggered for one record
        action = {
            'name': _('Size Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line.size',
            'view_mode': 'tree,form',
            'domain': [('line_id', '=', self.id)],  # Filter to show only related sizes
            'context': {
                'default_order_line_id': self.id,
                'default_customizable': self.customizable,
                'default_quantity': self.quantity,
                'default_existing_customization': self.client_customization
                # Pre-fill the relation field
            },
            'target': 'current'
        }
        return action

    def action_client_command_wizard(self):
        """
        Action pour ouvrir le wizard .
        """
        return {
            'name': 'Personnaliser command',
            'type': 'ir.actions.act_window',
            'res_model': 'client.command',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_line_id': self.id,
                'default_customizable': self.customizable,
                'default_quantity': self.quantity,
                'default_existing_customization': self.client_customization
            }
        }
