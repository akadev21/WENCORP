from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)  # Initialize logger


class CustomCommandWizard(models.TransientModel):
    _name = 'client.command'
    _description = 'Wizard pour personnaliser les commandes des produits'

    # Link to the wizard line model using One2many
    wizard_line_ids = fields.One2many('client.command.wizard.line', 'wizard_id', string="Rows")
    order_line_id = fields.Many2one('sale.order.line', string="Ligne de commande", required=True)
    customizable = fields.Boolean(string="Personnalisable")
    quantity = fields.Float(
        string="Quantité prévue",
        readonly=True
    )
    total_number_input = fields.Float(
        string="Total Nombre d'Entrées",
        compute='_compute_total_number_input',
        store=True
    )

    @api.depends('wizard_line_ids.number_input')
    def _compute_total_number_input(self):
        """
        Compute the total sum of `number_input` fields in `wizard_line_ids`.
        """
        for record in self:
            record.total_number_input = sum(line.number_input for line in record.wizard_line_ids)

    @api.constrains('wizard_line_ids')
    def _check_quantity(self):
        """
        Validate that the sum of `number_input` matches the `quantity`.
        If the sum of `number_input` equals `quantity`, prevent adding new lines.
        """
        total_number_input = sum(line.number_input for line in self.wizard_line_ids)

        if total_number_input > self.quantity:
            raise UserError(
                f"La somme des valeurs de 'Nombre' ({total_number_input}) dépasse la quantité ({self.quantity})."
            )
        if total_number_input == self.quantity:
            raise UserError(
                f"La somme des valeurs de 'Nombre' ({total_number_input}) est déjà égale à la quantité ({self.quantity}). Vous ne pouvez pas ajouter plus de lignes."
            )

    def add_line(self):
        """
        Custom method to handle the addition of a new line. It checks whether the sum
        of 'number_input' has reached the 'quantity'. If so, it blocks the addition.
        """
        total_number_input = sum(line.number_input for line in self.wizard_line_ids)
        if total_number_input >= self.quantity:
            raise UserError(
                "La somme des valeurs de 'Nombre' a atteint ou dépasse la quantité. Vous ne pouvez pas ajouter de nouvelles lignes."
            )
        # Continue adding the line
        self.wizard_line_ids = [(0, 0, {'size': 'xs'})]  # You can replace the default field values as per your logic

    def apply_changes(self):
        """
        Appliquer les changements dans le contexte du wizard, sans affecter la ligne de commande.
        """
        if self.order_line_id:
            # Log the order_line_id to verify the data
            _logger.info(f"Applying changes to Order Line {self.order_line_id.id}")

            # Prepare a list to store the customizations applied within the wizard
            customizations_applied = []

            for line in self.wizard_line_ids:
                if line.text_field:
                    # Log individual line data for debugging
                    _logger.info(
                        f"Customization: {line.text_field}, Size: {line.size}, Number: {line.number_input}")

                    # Collect the customization data
                    customizations_applied.append({
                        'size': line.size,
                        'number_input': line.number_input,
                        'text_field': line.text_field
                    })

            # Optionally, log the applied customizations
            _logger.info(f"Customizations applied in wizard: {customizations_applied}")

            # You can add any further operations based on this data without saving to the order line
            # For example, you could create a custom record or handle it differently
            # In this example, we're just logging the data for debugging purposes.

            # Return to close the wizard
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

    def action_customize_line_wizard(self):
        """
        Opens a new wizard for customizing the line's text and number input.
        """
        return {
            'name': 'Personnaliser command text',
            'type': 'ir.actions.act_window',
            'res_model': 'client.command.name',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_wizard_id': self.id,
                'default_number_input': self.number_input,
            }
        }
