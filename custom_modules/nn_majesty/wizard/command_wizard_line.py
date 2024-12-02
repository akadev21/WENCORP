from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)  # Initialize logger


class ClientCommandNams(models.TransientModel):
    _name = 'client.command.name'
    _description = 'Wizard for Customizing Command Line'

    wizard_id = fields.Many2one('client.command.wizard.line', string="Parent Line", required=True)
    number_input = fields.Integer("Number Input", required=True)
    custom_text = fields.Char("Custom Text", required=True)

    def save_customization(self):
        """
        Apply the changes to the parent line and close the wizard.
        """
        if self.wizard_id:
            self.wizard_id.write({
                'number_input': self.number_input,
                'text_field': self.custom_text,
            })
            return {'type': 'ir.actions.act_window_close'}
        else:
            raise UserError("No parent line found to apply changes.")
