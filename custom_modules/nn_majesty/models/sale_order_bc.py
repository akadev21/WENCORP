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
        """
        Confirmer le bon de commande et mettre à jour l'état du projet commercial.
        """
        self.ensure_one()  # Ensure we're working with a single record
        _logger.info(f"Tentative de confirmation BC pour la commande {self.id}")

        if not self.project_id:
            _logger.warning(f"Aucun projet commercial trouvé pour la commande {self.id}.")
            raise UserError("Aucun projet commercial n'a été trouvé pour cette commande.")

        try:
            _logger.info(
                f"Project ID associated with sale order {self.id}: {self.project_id.id} - {self.project_id.name}")

            # Update project state
            self.project_id.write({
                'state_commercial': 'bc_confirme'
            })

            # Confirm the sale order
            self.action_confirm()

            _logger.info(f"Commande confirmée pour le projet commercial {self.project_id.reference}.")

            return True

        except UserError as ue:
            _logger.error(f"Erreur utilisateur lors de la confirmation du BC: {str(ue)}")
            raise ue
        except Exception as e:
            _logger.error(f"Erreur lors de la confirmation du BC: {str(e)}")
            raise UserError(f"Erreur lors de la confirmation du bon de commande: {str(e)}")


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

    upload_bat_design = fields.Binary(
        string="Upload BAT",
        attachment=True,
        help="Téléchargement du bon à tirer"
    )
    bat_design_name = fields.Char(
        string="Nom du design BAT",
        required=True
    )

    def action_client_command_wizard(self):
        """
        Action pour ouvrir le wizard de personnalisation du nom.
        """
        return {
            'name': 'Personnaliser le Nom',
            'type': 'ir.actions.act_window',
            'res_model': 'client.command',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_line_id': self.id
            }
        }
