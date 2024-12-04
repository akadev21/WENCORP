from odoo import _, api, fields, models
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
        readonly=False  # Typically set to readonly because it's a related field
    )

    # Assuming there's a relationship to the product.template model
    product_id = fields.Many2one('product.template', string='Nom d\'article ')
    usine = fields.Many2one('res.users')
    # Quantité
    quantity = fields.Integer(string='Quantité prévue')
    project_id = fields.Many2one('commercial.project', string='#')
    desginer_id = fields.Many2one('designer.project')
    reference = fields.Many2one(
        related='desginer_id.reference_projet',
        string="Référence",
        readonly=True
    )

    state_commercial = fields.Selection(
        related="project_id.state_commercial",
        string="State Commercial",
        readonly=True,

    )

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
    model_design_2_v = fields.Binary(string="Modèle design", attachment=True)
    model_design_filename_2_v = fields.Char(string="BAT Filename")
    upload_bat_design = fields.Binary(string="Upload BAT Prod", attachment=True)
    bat_design_name = fields.Char()
    size_ids = fields.One2many(
        'sale.order.line.size',
        'line_id',
        string="Sizes and Quantities"
    )

    def open_line_details(self):

        self.ensure_one()
        action = {
            'name': _('Size Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line.size',
            'view_mode': 'tree,form',
            'context': {
                'default_order_line_id': self.id,
                'default_customizable': self.customizable,
                'default_quantity': self.quantity,


            },
            'target': 'new'
        }
        return action
