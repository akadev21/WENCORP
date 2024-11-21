from odoo import models, fields, api
import os


class MajestyProducts(models.Model):
    _name = 'commercial.products'
    _description = 'Majesty Products'

    # Référence (article reference from product.template)

    # Modèles
    description_sale = fields.Text(
        string='Description ',
        related='product_id.description_sale',  # Relating to the product.template's description_sale
        store=True,  # Optionally, make it stored in the database for faster access
        readonly=True  # Typically set to readonly because it's a related field
    )

    # Assuming there's a relationship to the product.template model
    product_id = fields.Many2one('product.template', string='Nom d\'article ')
    usine = fields.Many2one('res.users', racking=True)
    # Quantité
    quantity = fields.Integer(string='Quantité prévue')
    project_id = fields.Many2one('commercial.project', string='#')
    desginer_id = fields.Many2one('designer.project')
    reference = fields.Many2one(
        related='desginer_id.reference_projet',
        string="Référence",
        readonly=True
    )
    state_commercial = fields.Selection(related="project_id.state_commercial")

    # Sexe (    male, female, not chosen)
    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('unisex', 'H/F')
    ], string='Sexe', default='unisex')

    # Customizable (boolean)
    customizable = fields.Boolean(string='personnalisable')
    quantity_delivered = fields.Integer(string='Quantité livrée')

    # Description of the article
    description = fields.Text(string='Description de l\'article')
    model_design = fields.Binary(string="Modèle design", attachment=True)
    model_design_filename = fields.Char(string="BAT Filename")

    # model_design_image = fields.Binary(compute="_compute_model_design_image", string="Modèle design")
    #
    # @api.depends('model_design')
    # def _compute_model_design_image(self):
    #     for record in self:
    #         record.model_design_image = record.model_design
    #
    #
    # @api.depends('model_design_image')
    # def _compute_show_model_design_image(self):
    #     for record in self:
    #         if record.show_model_design_image:
    #             record.show_model_design_image = True
    #
    # show_model_design_image = fields.Boolean(compute="_compute_show_model_design_image", store=True)
    #
    # @api.onchange('model_design_filename')
    # def _compute_show_model_design_image(self):
    #     image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg']
    #     for record in self:
    #         if record.model_design_filename:
    #             if any(record.model_design_filename.lower().endswith(ext) for ext in image_extensions):
    #                 record.show_model_design_image = True
    #             else:
    #                 record.show_model_design_image = False
