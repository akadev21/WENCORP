from odoo import _, api, fields, models

from datetime import datetime
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLineSize(models.Model):
    _name = 'sale.order.line.size'
    _description = 'Size and Quantity Details for Sale Order Line'

    size = fields.Selection([
        ('xs', 'XS'),
        ('s', 'S'),
        ('m', 'M'),
        ('l', 'L'),
        ('xl', 'XL'),
        ('xxl', 'XXL'),
        ('xxxl', 'XXXL'),
    ], string="Size", required=True)

    quantity = fields.Integer(string="Quantity", required=True, )
    quantity_size = fields.Integer(string="Quantity", required=False, help="Quantity for the size")

    line_id = fields.Many2one(
        'sale.order.line',
        string="Sale Order Line",
        ondelete='cascade',
        required=False,
        default=lambda self: self._context.get('default_order_line_id'),
    )
    name_ids = fields.One2many(
        'sale.order.line.size.name',
        'size_id',
        string="Names",
        help="List of names associated with this size"
    )
    total_quantity_size = fields.Integer(
        string="Total Quantity Size",
        compute='_compute_total_quantity_size',
        store=True
    )

    @api.depends('quantity_size')  # Depends on quantity_size in the same model
    def _compute_total_quantity_size(self):
        for record in self:
            # The total_quantity_size is just the sum of quantity_size for all related size lines
            record.total_quantity_size = record.quantity_size

    @api.onchange('quantity_size')
    def _onchange_quantity(self):
        """Generate name_ids dynamically based on quantity."""
        if self.quantity_size > 0:
            # Generate `quantity` number of name_ids dynamically
            names = []
            for i in range(self.quantity_size):
                names.append((0, 0, {'name': f'Name {i + 1}'}))  # Creating names "Name 1", "Name 2", etc.
            self.name_ids = names
        else:
            # If quantity is set to 0 or negative, clear name_ids
            self.name_ids = []

    def create(self, vals):
        # Get the `quantity` and `quantity_size` from the values to be created
        quantity = vals.get('quantity', 0)
        total_quantity_size = vals.get('total_quantity_size', 0)

        # If `total_quantity_size` equals `quantity`, raise a validation error
        if total_quantity_size == quantity:
            raise UserError("The total quantity size cannot equal the quantity.")

        return super(SaleOrderLineSize, self).create(vals)

    def unlink(self):
        for record in self:
            if record.name_ids:  # Check if there are associated name records
                raise UserError(
                    _("You cannot delete this size entry because it has associated names. Please archive it instead."))
        return super(SaleOrderLineSize, self).unlink()
