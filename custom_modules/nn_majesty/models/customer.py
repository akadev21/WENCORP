from odoo import models, fields, api


class ClientInherit(models.Model):
    _inherit = 'res.partner'
