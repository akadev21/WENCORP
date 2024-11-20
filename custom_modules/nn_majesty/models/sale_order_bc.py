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
    # usine
    usine = fields.Many2one('res.users', racking=True)
    # Description of the article
    description = fields.Text(string='Description de l\'article')

    # Model design (Binary field for attachments)
    model_design = fields.Binary(string="Modèle design", attachment=True)

    # Filename for the BAT (Bon à tirer)
    model_design_filename = fields.Char(string="BAT Filename")

    def action_create_usin_project(self):
        for order in self:
            if not order.order_line:
                raise UserError(_("La commande de vente ne contient aucune ligne d'article."))

            # Create the usine project
            usin_project_vals = {
                'reference': f'UP-{order.name}',
                'date_livraison': fields.Datetime.now(),
                'sale_order_id': order.id,
                'line_ids': [
                    (0, 0, {'sale_order_line_id': line.id}) for line in order.order_line
                ],
            }
            usin_project = self.env['usin.project'].create(usin_project_vals)

            # Send email notification to the usine
            template_id = self.env.ref('nn_majesty.email_template_usin_notification').id
            if template_id:
                self.env['mail.template'].browse(template_id).send_mail(order.id, force_send=True)

            # Log action in Chatter
            order.message_post(
                body=_(
                    f"Projet Usine créé: {usin_project.reference} <br>"
                    f"- {len(order.order_line)} lignes copiées <br>"
                    f"- Notification envoyée à l'usine."
                )
            )
        return True