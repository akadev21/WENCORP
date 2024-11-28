from odoo import models, fields, api


class CustomCommandWizard(models.TransientModel):
    _name = 'client.command'
    _description = 'Wizard pour personnaliser les commandes des produits'

    # Link to the wizard line model using One2many
    wizard_line_ids = fields.One2many('client.command.wizard.line', 'wizard_id', string="Rows")
    order_line_id = fields.Many2one('sale.order.line', string="Ligne de commande", required=True)

    def apply_changes(self):
        """
        Appliquer les changements à la ligne de commande.
        """
        if self.order_line_id:
            # Log the order_line_id and wizard lines to verify the data
            _logger.info(f"Applying changes to Order Line {self.order_line_id.id}")

            for line in self.wizard_line_ids:
                if line.text_field:
                    # Log individual line data for debugging
                    _logger.info(
                        f"Applying customization: {line.text_field}, Size: {line.size}, Number: {line.number_input}")

                    # Apply the changes to the order line
                    self.order_line_id.write({
                        'text_field': line.text_field,
                        'size': line.size,
                        'number_input': line.number_input,
                    })
            return {'type': 'ir.actions.act_window_close'}
        else:
            _logger.error("No order line found to apply changes.")
            raise UserError("Aucune ligne de commande trouvée pour appliquer les changements.")


class ClientCommandWizardLine(models.TransientModel):
    _name = 'client.command.wizard.line'
    _description = 'Client Command Wizard Line'

    wizard_id = fields.Many2one('client.command', string="Wizard Reference", required=True)
    size = fields.Selection([
        ('xs', 'XS'),
        ('s', 'S'),
        ('m', 'M'),
        ('l', 'L'),
        ('xl', 'XL'),
        ('xxl', 'XXL'),
        ('xxxl', 'XXXL'),
    ], string="Size", required=True)
    number_input = fields.Integer("Enter Number")
    text_field = fields.Char("Enter les nom", store=True)
