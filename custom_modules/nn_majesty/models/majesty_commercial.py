from odoo import models, fields

class MajestyCommercial(models.Model):
    _name = 'majesty.commercial'
    _description = 'Majesty Commercial'

    commercial_id = fields.Many2one('res.users', string="Commercial")
    project_id = fields.Many2one('majesty.project', string="Project")
