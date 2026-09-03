from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(
        string='Is Customer',
        default=False,
        help='Check if this contact is a customer'
    )
    is_supplier = fields.Boolean(
        string='Is Supplier',
        default=False,
        help='Check if this contact is a supplier'
    )
    is_agency = fields.Boolean(
        string='Is Agency',
        default=False,
        help='Check if this contact is an agency'
    )
