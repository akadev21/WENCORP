from odoo import models, fields

class MajestyProducts(models.Model):
    _name = 'majesty.products'
    _description = 'Majesty Products'

    # Référence (article reference from product.template)

    # Modèles
    model_name = fields.Char(string='Nom Modèles', required=True)

    # Quantité
    quantity = fields.Integer(string='Quantité prévue')
    project_id = fields.Many2one('majesty.project', string='Project')

    # Sexe (male, female, not chosen)
    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('not_chosen', 'Non choisi')
    ], string='Sexe', default='not_chosen')

    # Customizable (boolean)
    customizable = fields.Boolean(string='Customisable')

    # Description of the article
    description = fields.Text(string='Description de l\'article')

    # Link to the product.template model (related field)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
