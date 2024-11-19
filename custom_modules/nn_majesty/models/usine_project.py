from odoo import models, fields, api
from odoo.exceptions import UserError


class UsinProject(models.Model):
    _name = 'usin.project'
    _description = 'Usin Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add Chatter support
    _rec_name = 'reference'

    reference = fields.Char(string="Référence", required=True, tracking=True)
    date_livraison = fields.Datetime(string="Date de Livraison", required=True, tracking=True)

    status_usin = fields.Selection(
        [
            ('attribuee', 'Attribuée'),
            ('confirmee', 'Confirmée'),
            ('validee', 'Validée'),
            ('rejet', 'Rejetée'),
            ('production', 'Production'),
            ('pre_expedition', 'Pré-Expédition'),
        ],
        string="Statut Usine",
        default='attribuee',
        tracking=True
    )

    commercial = fields.Many2one(
        'res.users',
        string='Commercial',
        default=lambda self: self.env.user,
        readonly=True
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string="Bon de Commande",
        required=True,
        help="Lien vers le bon de commande associé"
    )

    line_ids = fields.One2many(
        'usin.project.line',
        'usin_project_id',
        string="Lignes de Produit"
    )

    def action_confirm(self):
        """Confirm the project and change status to 'Confirmée'."""
        if not self.line_ids:
            raise UserError("Aucune ligne de produit n'est associée à ce projet.")
        self.status_usin = 'confirmee'

    def action_validate(self):
        """Validate the project and change status to 'Validée'."""
        if self.status_usin != 'confirmee':
            raise UserError("Le projet doit d'abord être confirmé.")
        self.status_usin = 'validee'


class UsinProjectLine(models.Model):
    _name = 'usin.project.line'
    _description = 'Usin Project Line'

    usin_project_id = fields.Many2one(
        'usin.project',
        string="Projet Usine",
        ondelete='cascade',
        required=True
    )
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string="Ligne Bon de Commande",
        required=True,
        help="Lien vers la ligne de bon de commande associée"
    )
    product_id = fields.Many2one(
        related='sale_order_line_id.product_id',
        string="Produit",
        readonly=True
    )
    quantity = fields.Float(
        related='sale_order_line_id.product_uom_qty',
        string="Quantité",
        readonly=True
    )
    description = fields.Text(
        related='sale_order_line_id.description',
        string="Description",
        readonly=True
    )
    status_line = fields.Selection(
        [
            ('pending', 'En Attente'),
            ('produced', 'Produit'),
            ('rejected', 'Rejetée'),
        ],
        string="Statut de Ligne",
        default='pending',
        tracking=True
    )
