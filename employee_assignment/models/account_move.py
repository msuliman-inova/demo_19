from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    assigned_employee_id = fields.Many2one(
        'hr.employee',
        string='Assigned Employee',
        tracking=True,
        readonly=False,
        states={'posted': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Employee assigned to this invoice/bill'
    )

    # Partner type related fields
    partner_is_customer = fields.Boolean(
        related='partner_id.is_customer',
        string='Customer',
        readonly=True
    )
    partner_is_supplier = fields.Boolean(
        related='partner_id.is_supplier',
        string='Supplier',
        readonly=True
    )
    partner_is_agency = fields.Boolean(
        related='partner_id.is_agency',
        string='Agency',
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        """Set current user's employee as default assigned employee"""
        res = super().default_get(fields_list)
        if 'assigned_employee_id' in fields_list:
            employee = self.env.user.employee_id
            if employee:
                res['assigned_employee_id'] = employee.id
        return res
