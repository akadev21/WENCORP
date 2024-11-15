from odoo import models, fields, api


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one(
        'commercial.project',
        string="Projet Commercial",
        ondelete='cascade'
    )
    reference = fields.Char(tracking=True, string='Reference')  # Enable tracking to log changes in Chatter
    active = fields.Boolean(default=True)



class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    # Sexe (male, female, not chosen)
    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('unisex', 'H/F')
    ], string='Sexe', default='unisex')

    # Customizable (boolean)
    customizable = fields.Boolean(string='Personnalisable')

    # Description of the article
    description = fields.Text(string='Description de l\'article')

    # Model design (Binary field for attachments)
    model_design = fields.Binary(string="Modèle design", attachment=True)

    # Filename for the BAT (Bon à tirer)
    model_design_filename = fields.Char(string="BAT Filename")