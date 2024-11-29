from odoo import models, fields, api
from odoo.exceptions import UserError


class UsineProject(models.Model):
    _name = 'usine.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Usine Project"
    _rec_name = 'reference_projet'

    reference_projet = fields.Many2one(
        'commercial.project',
        string="Projet Référence",
        required=True,
        help="Référence du projet associé",
        tracking=True
    )
    reference = fields.Char(
        string="Référence",
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('usine.project'),
        tracking=True
    )
    date_livraison = fields.Datetime(
        string="Date de Livraison",
        required=False,
        tracking=True
    )
    status_usin = fields.Selection([
        ('attribuee', 'Attribuée'),
        ('confirmee', 'Confirmée'),
        ('validee', 'Validée'),
        ('rejet', 'Rejetée'),
        ('production', 'Production'),
        ('pre_expedition', 'Pré-Expédition'),
    ], string="Statut Usine", default='attribuee', tracking=True)
    commercial = fields.Many2one(
        'res.users',
        string="Commercial",
        required=True,
        help="Utilisateur commercial assigné au projet"
    )
    creation_date = fields.Date(
        string="Date de Création",
        default=fields.Date.context_today,
        tracking=True
    )
    product_ids = fields.One2many(
        'usine.products',
        'usine_id',
        string="Produits",
        help="Produits associés à ce projet usine"
    )
    notes = fields.Text(string="Notes Internes", help="Notes ou commentaires sur le projet usine.")
    is_favorite = fields.Boolean('Ajouter aux favoris')

    @api.model
    def create(self, vals):
        if not vals.get('reference'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('usine.project')
        return super(UsineProject, self).create(vals)

    def action_confirm(self):
        """Confirm the project and change status to 'Confirmée'."""
        for record in self:
            if not record.product_ids:
                raise UserError("Aucun produit n'est associé à ce projet.")
            record.status_usin = 'confirmee'
            record.message_post(body="Projet confirmé")

    def action_validate(self):
        """Validate the project and change status to 'Validée'."""
        for record in self:
            if record.status_usin != 'confirmee':
                raise UserError("Le projet doit d'abord être confirmé.")
            record.status_usin = 'validee'
            record.message_post(body="Projet validé")


class UsineProducts(models.Model):
    _name = 'usine.products'
    _description = "Produits Usine"

    usine_id = fields.Many2one(
        'usine.project',
        string="Projet Usine",
        ondelete='cascade',
        required=True,
        help="Projet usine auquel ce produit est lié"
    )
    product_id = fields.Many2one(
        'product.product',
        string="Produit",
        required=True,
        help="Produit associé"
    )
    status_usin = fields.Selection([
        ('attribuee', 'Attribuée'),
        ('confirmee', 'Confirmée'),
        ('validee', 'Validée'),
        ('rejet', 'Rejetée'),
        ('production', 'Production'),
        ('pre_expedition', 'Pré-Expédition'),
    ], string="Statut Usine", default='attribuee', tracking=True)
    quantity = fields.Float(string="Quantité", required=True)
    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('unisex', 'H/F')
    ], string='Sexe', default='unisex')
    quantity_delivered = fields.Float(string="Quantité Livrée")
    customizable = fields.Boolean(string="Personnalisable")
    usine = fields.Char(string="Usine")
    description = fields.Text(string="Description")
    model_design = fields.Binary(string="Design du Modèle", attachment=True)
    model_design_filename = fields.Char(string="Nom du Fichier Design")
    model_design_2_v = fields.Binary(string="Modèle design", attachment=True)
    model_design_filename_2_v = fields.Char(string="BAT Filename")
    upload_bat_design = fields.Binary(string="Upload BAT", attachment=True)
    bat_design_name = fields.Char(required=True)

    _sql_constraints = [
        ('unique_product_per_usine', 'unique(usine_id, product_id)',
         'Chaque produit doit être unique pour ce projet usine.')
    ]
