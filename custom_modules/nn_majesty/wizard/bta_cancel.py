from odoo import models, fields, api
from odoo.exceptions import UserError

class WizardInvalidateDesigner(models.TransientModel):
    _name = 'wizard.invalidate.designer'
    _description = 'Wizard to Invalidate Designer'

    invalidate_reason = fields.Text(string="Raison d'invalidation", required=True, help="Indiquer la raison de l'invalidation")
    project_id = fields.Many2one('commercial.project', string="Projet", required=True)

    def confirm_invalidate_designer(self):
        self.ensure_one()
        if not self.project_id:
            raise UserError("Le projet n'est pas spécifié.")

        # Update project state and reset designer fields
        self.project_id.write({
            'state_commercial': 'preparation',
            'designer': False,
            'designer_assign_date': False,
            'invalidation_reason': self.invalidate_reason,
        })

        # Log the invalidation in the chatter
        self.project_id.message_post(
            body=f"Designer invalidé : {self.invalidate_reason}"
        )
        return {'type': 'ir.actions.act_window_close'}

    def confirm_cancel_reason_da(self):
        self.ensure_one()
        self.da_id.write({
            'state': 'nonvalide',
            'motif_validation_da': self.cancel_reason
        })
        return {'type': 'ir.actions.act_window_close'}