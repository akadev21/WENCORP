from odoo import models, fields, api
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

    def action_confirm_bc(self):

        for order in self:
            try:

                project_updates = {
                    'state_commercial': 'bc_confirme',

                }

                for line in order.order_line:
                    if line.gender:
                        project_updates['quantity'] = line.quantity

                order.project_id.write(project_updates)

                # Log the update in the project Chatter
                order.project_id.message_post(
                    body=f"""Bon de commande confirmé :
                    - État mis à jour : 'BC Confirmé'
                    - Référence : {order.reference}
                    - Fichier BAT : {order.bat_filename or 'Non spécifié'}
                    - Sexe: {project_updates.get('gender', 'Non spécifié')}
                    - Personnalisable: {project_updates.get('customizable', 'Non spécifié')}""",
                    message_type='notification'
                )

                # Optionally log in the Sale Order Chatter
                order.message_post(
                    body=f"Bon de commande confirmé. Projet lié mis à jour ({order.project_id.reference})."
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
                'default_quantity': self.quantity
            }
        }
