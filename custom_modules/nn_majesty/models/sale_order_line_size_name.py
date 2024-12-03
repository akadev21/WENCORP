from odoo import _, api, fields, models

from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLineSizeName(models.Model):
    _name = 'sale.order.line.size.name'
    _description = 'Names Associated with Sale Order Line Size'

    name = fields.Char(string="Name", required=True, help="Name for the size and quantity entry")
    size_id = fields.Many2one(
        'sale.order.line.size',
        string="Size and Quantity",
        ondelete='cascade',
        required=True
    )
