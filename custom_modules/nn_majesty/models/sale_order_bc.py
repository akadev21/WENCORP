from odoo import models, fields, api


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    reference = fields.Char(tracking=True,string='Reference')  # Enable tracking to log changes in Chatter

