from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    assigned_employee_id = fields.Many2one(
        'hr.employee',
        string='Assigned Employee',
        tracking=True,
        readonly=False,
        states={'sale': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Employee assigned to this sale order'
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

    def _prepare_invoice(self):
        """Propagate assigned employee to invoice"""
        invoice_vals = super()._prepare_invoice()
        if self.assigned_employee_id:
            invoice_vals['assigned_employee_id'] = self.assigned_employee_id.id
        return invoice_vals
