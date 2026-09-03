from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    assigned_employee_id = fields.Many2one(
        'hr.employee',
        string='Assigned Employee',
        tracking=True,
        help='Employee assigned to this lead/opportunity'
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
