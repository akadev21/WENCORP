from odoo import models, fields, api
from odoo.exceptions import UserError


class UsinProject(models.Model):
    _name = 'usin.project'
    _description = 'Usin Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'

    reference_projet = fields.Many2one('commercial.project', string='Référence Projet')
    reference = fields.Char(string="Référence", required=True, tracking=True)
    date_livraison = fields.Datetime(string="Date de Livraison", required=True, tracking=True)
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
        domain="[('order_id', '=', parent.sale_order_id)]",
        help="Lien vers la ligne de bon de commande associée"
    )

    product_id = fields.Many2one(
        'product.product',  # Changed from product.template to product.product
        string="Produit",
        related='sale_order_line_id.product_id',
        store=True,
        readonly=True
    )

    quantity = fields.Float(
        related='sale_order_line_id.product_uom_qty',
        string="Quantité",
        store=True,
        readonly=True
    )

    description = fields.Text(
        related='sale_order_line_id.name',  # Changed from description to name
        string="Description",
        store=True,
        readonly=True
    )

    status_line = fields.Selection([
        ('pending', 'En Attente'),
        ('produced', 'Produit'),
        ('rejected', 'Rejetée'),
    ], string="Statut de Ligne", default='pending', tracking=True)


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one(
        'commercial.project',
        string="Projet Commercial",
        ondelete='restrict'  # Changed from cascade to restrict
    )
    reference = fields.Char(tracking=True, string='Reference')
    active = fields.Boolean(default=True)

    def action_create_usin_project(self):
        self.ensure_one()
        if not self.order_line:
            raise UserError("Le bon de commande doit avoir des lignes de commande.")

        vals = {
            'reference': f'UP-{self.name}',
            'date_livraison': fields.Datetime.now(),
            'sale_order_id': self.id,
            'line_ids': [(0, 0, {
                'sale_order_line_id': line.id
            }) for line in self.order_line]
        }

        usin_project = self.env['usin.project'].create(vals)
        self.message_post(body=f"Projet Usine créé: {usin_project.reference}")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Projet Usine',
            'res_model': 'usin.project',
            'res_id': usin_project.id,
            'view_mode': 'form',
            'target': 'current',
        }


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    gender = fields.Selection([
        ('male', 'Homme'),
        ('female', 'Femme'),
        ('unisex', 'H/F')
    ], string='Sexe', default='unisex')

    customizable = fields.Boolean(string='Personnalisable')
    usine = fields.Many2one('res.users', tracking=True)  # Fixed typo in tracking
    description = fields.Text(string='Description de l\'article')
    model_design = fields.Binary(string="Modèle design", attachment=True)
    model_design_filename = fields.Char(string="BAT Filename")
