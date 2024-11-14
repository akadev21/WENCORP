from odoo import models, fields


class MajestyProducts(models.Model):
    _name = 'commercial.products'
    _description = 'Majesty Products'

    # Référence (article reference from product.template)

    # Modèles
    description_sale = fields.Text(
        string='Description de vente',
        related='product_id.description_sale',  # Relating to the product.template's description_sale
        store=True,  # Optionally, make it stored in the database for faster access
        readonly=True  # Typically set to readonly because it's a related field
    )

    # Assuming there's a relationship to the product.template model
    product_id = fields.Many2one('product.template', string='Product Template')

    # Quantité
    quantity = fields.Integer(string='Quantité prévue')
    project_id = fields.Many2one('commercial.project', string='Project')

    # Sexe (male, female, not chosen)
    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('unisex', 'H/F')
    ], string='Sexe', default='unisex')

    # Customizable (boolean)
    customizable = fields.Boolean(string='personnalisable')

    # Description of the article
    description = fields.Text(string='Description de l\'article')
    model = fields.Binary(attachment=True)
    model_filename = fields.Char("Filename")
    # Link to the product.template model (related field)
