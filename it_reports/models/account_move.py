from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    delivery_order_number = fields.Char(string='DO Number', copy=False)
