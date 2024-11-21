from odoo import models, fields, api
from odoo.exceptions import UserError


class UsineProject(models.Model):
    _name = 'usine.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Usine Project"
    _rec_name = 'reference_projet'  # Display the reference project name as the main field

    reference_projet = fields.Many2one(
        'commercial.project',
        string="Projet Référence",
        required=True,
        help="Référence du projet associé",
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

    @api.model
    def create(self, values):
        # Ensure a reference project is linked
        if 'reference_projet' not in values or not values['reference_projet']:
            raise UserError("Une référence de projet est requise pour créer un projet usine.")

        # Call the super method to create the record
        return super(UsineProject, self).create(values)


class UsineProducts(models.Model):
    _name = 'usine.products'
    _description = "Produits Usine"
    reference = fields.Char(string="Référence", required=True, tracking=True)
    date_livraison = fields.Datetime(string="Date de Livraison", required=True, tracking=True)
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
    gender = fields.Selection(
        [('male', 'Homme'), ('female', 'Femme')],
        string="Genre",
        required=True
    )
    quantity_delivered = fields.Float(string="Quantité Livrée")
    customizable = fields.Boolean(string="Personnalisable")
    usine = fields.Char(string="Usine")
    description = fields.Text(string="Description")
    model_design = fields.Binary(string="Design du Modèle", attachment=True)
    model_design_filename = fields.Char("Nom du Fichier Design")

    @api.model
    def create(self, vals):
        if 'reference' not in vals:
            vals['reference'] = self.env['ir.sequence'].next_by_code('usin.project.sequence')
        return super(UsinProject, self).create(vals)

    def action_confirm(self):
        """Confirm the project and change status to 'Confirmée'."""
        for record in self:
            if not record.line_ids:
                raise UserError("Aucune ligne de produit n'est associée à ce projet.")
            record.status_usin = 'confirmee'
            record.message_post(body="Projet confirmé")

    def action_validate(self):
        """Validate the project and change status to 'Validée'."""
        for record in self:
            if record.status_usin != 'confirmee':
                raise UserError("Le projet doit d'abord être confirmé.")
            record.status_usin = 'validee'
            record.message_post(body="Projet validé")

    _sql_constraints = [
        ('unique_product_per_usine', 'unique(usine_id, product_id)',
         'Chaque produit doit être unique pour ce projet usine.')
    ]
