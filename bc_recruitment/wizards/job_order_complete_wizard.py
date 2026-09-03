# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class JobOrderCompleteWizard(models.TransientModel):
    _name = 'job.order.complete.wizard'
    _description = 'Job Order Complete Confirmation Wizard'

    job_order_id = fields.Many2one('bc.job.order', string='Job Order', required=True, readonly=True)
    positions_requested = fields.Integer(string='Positions Requested', related='job_order_id.positions_requested', readonly=True)
    positions_filled = fields.Integer(string='Positions Filled', related='job_order_id.positions_filled', readonly=True)
    positions_remaining = fields.Integer(string='Positions Remaining', related='job_order_id.positions_remaining', readonly=True)
    confirm_completion = fields.Boolean(string='I agree to mark this job order as completed even though not all positions are filled', default=False)

    def action_confirm_complete(self):
        """Confirm and mark job order as completed"""
        self.ensure_one()

        if not self.confirm_completion:
            raise UserError(_('You must confirm that you want to mark this job order as completed.'))

        # Mark job order as completed
        self.job_order_id.write({
            'state': 'completed',
            'completion_date': fields.Date.today()
        })

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancel the wizard"""
        return {'type': 'ir.actions.act_window_close'}
