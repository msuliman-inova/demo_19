from odoo import api, fields, models, _


class StageChangeConfirmWizard(models.TransientModel):
    _name = 'stage.change.confirm.wizard'
    _description = 'Stage Change Confirmation Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    new_stage_id = fields.Many2one('crm.stage', string='New Stage', required=True)
    assigned_employee_id = fields.Many2one(
        'hr.employee',
        string='Assigned Employee',
        related='lead_id.assigned_employee_id',
        readonly=True,
    )
    message = fields.Text(string='Message', readonly=True)

    def action_confirm(self):
        """Confirm the stage change"""
        self.ensure_one()
        # Bypass validation by using context flag
        self.lead_id.with_context(skip_stage_validation=True).write({
            'stage_id': self.new_stage_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}
