# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BCPlacement(models.Model):
    _name = 'bc.placement'
    _description = 'Worker Placement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    # Basic Information
    name = fields.Char(string='Placement Reference', required=True, copy=False, readonly=True,
                      default=lambda self: _('New'), tracking=True)

    job_order_id = fields.Many2one('bc.job.order', string='Job Order', required=True,
                                   ondelete='cascade', tracking=True)
    worker_id = fields.Many2one('bc.worker', string='Worker', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)

    sale_order_id = fields.Many2one('sale.order', string='Sale Order',
                                   related='job_order_id.sale_order_id', store=True)
    sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line',
                                   related='job_order_id.sale_line_id', store=True)
    product_id = fields.Many2one('product.product', string='Product',
                                 related='job_order_id.product_id', store=True)

    # Job Details
    job_title = fields.Char(string='Job Title', related='job_order_id.job_title', store=True)
    work_location = fields.Char(string='Work Location', related='job_order_id.work_location', store=True)

    # Contract Details
    contract_type = fields.Selection([
        ('permanent', 'Permanent'),
        ('temporary', 'Temporary'),
        ('contract', 'Contract'),
        ('seasonal', 'Seasonal')
    ], string='Contract Type', required=True, default='contract')

    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    actual_end_date = fields.Date(string='Actual End Date', tracking=True)

    duration_months = fields.Integer(string='Duration (Months)', compute='_compute_duration', store=True)

    # Salary & Invoicing
    salary = fields.Monetary(string='Worker Salary', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    invoiced = fields.Boolean(string='Invoiced', default=False, readonly=True, copy=False)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False,
                                 help='The invoice that includes this placement')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    visa_status = fields.Selection([
        ('mol', 'MOL - Labor Approval'),
        ('immigration_typing', 'Immigration Typing'),
        ('immigration_approval', 'Immigration Approval'),
        ('visa_issued', 'Visa Issued')
    ], string='Visa Status', tracking=True, help='Current visa processing status')

    termination_reason = fields.Text(string='Termination Reason')
    termination_date = fields.Date(string='Termination Date')

    # Performance & Feedback
    performance_rating = fields.Selection([
        ('1', 'Poor'),
        ('2', 'Below Average'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Performance Rating')
    client_feedback = fields.Text(string='Client Feedback')

    # Other
    notes = fields.Text(string='Internal Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for placement in self:
            if placement.start_date and placement.end_date:
                delta = placement.end_date - placement.start_date
                placement.duration_months = delta.days // 30
            else:
                placement.duration_months = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bc.placement') or _('New')

            # Auto-assign placement if created from job order (has job_order_id and worker_id)
            if vals.get('job_order_id') and vals.get('worker_id') and vals.get('state') == 'draft':
                # Check if worker is available
                worker = self.env['bc.worker'].browse(vals['worker_id'])
                if worker.availability_status == 'available':
                    vals['state'] = 'assigned'

        return super().create(vals_list)

    def write(self, vals):
        """Update worker availability when placement state changes and auto-complete when visa issued"""
        # Track old states for delivered qty update
        old_states = {p.id: p.state for p in self} if 'state' in vals or vals.get('visa_status') == 'visa_issued' else {}

        # Auto-complete when visa status becomes 'visa_issued'
        if vals.get('visa_status') == 'visa_issued':
            for placement in self:
                if placement.state not in ['completed', 'terminated', 'cancelled']:
                    vals['state'] = 'completed'
                    if not vals.get('actual_end_date'):
                        vals['actual_end_date'] = fields.Date.today()

        result = super().write(vals)

        # Update worker availability based on new state
        if 'state' in vals:
            for placement in self:
                if placement.state in ['assigned', 'active']:
                    # Worker is now assigned/working
                    placement.worker_id.write({'availability_status': 'assigned'})
                elif placement.state == 'completed':
                    # Worker completed successfully - delivered to client permanently
                    placement.worker_id.write({'availability_status': 'unavailable'})
                elif placement.state in ['terminated', 'cancelled']:
                    # Worker returned or assignment cancelled - check if available
                    other_active = placement.worker_id.placement_ids.filtered(
                        lambda p: p.id != placement.id and p.state in ['assigned', 'active']
                    )
                    if not other_active:
                        placement.worker_id.write({'availability_status': 'available'})

        # Update delivered qty on sale order line when state changes to/from completed
        if old_states:
            self._update_delivered_qty(old_states)

        return result

    def _update_delivered_qty(self, old_states):
        """Update qty_delivered on related SO line when placements move to/from completed"""
        # Group changes by sale order line
        sale_lines_to_update = set()
        for placement in self:
            old_state = old_states.get(placement.id)
            new_state = placement.state
            if old_state == new_state:
                continue
            if not placement.sale_line_id:
                continue
            # State changed to or from completed
            if old_state == 'completed' or new_state == 'completed':
                sale_lines_to_update.add(placement.sale_line_id.id)

        # Recalculate delivered qty for affected sale order lines
        for sol in self.env['sale.order.line'].browse(list(sale_lines_to_update)):
            completed_count = self.search_count([
                ('sale_line_id', '=', sol.id),
                ('state', '=', 'completed'),
            ])
            sol.sudo().write({'qty_delivered': completed_count})

    def action_assign(self):
        """Assign worker to placement"""
        for placement in self:
            if placement.worker_id.availability_status not in ['available']:
                raise UserError(_('Worker %s is not available for assignment.') % placement.worker_id.name)

            if placement.job_order_id.positions_remaining <= 0:
                raise UserError(_('All positions for job order %s are already filled.') % placement.job_order_id.name)

            placement.write({'state': 'assigned'})

    def action_activate(self):
        """Activate the placement (worker has started)"""
        for placement in self:
            if placement.state != 'assigned':
                raise UserError(_('Only assigned placements can be activated.'))
            placement.write({'state': 'active'})

    def action_complete(self):
        """Complete the placement successfully"""
        for placement in self:
            if placement.state != 'active':
                raise UserError(_('Only active placements can be completed.'))

            placement.write({
                'state': 'completed',
                'actual_end_date': fields.Date.today()
            })

    def action_terminate(self):
        """Terminate the placement early"""
        for placement in self:
            if placement.state not in ['assigned', 'active']:
                raise UserError(_('Only assigned or active placements can be terminated.'))

            placement.write({
                'state': 'terminated',
                'termination_date': fields.Date.today(),
                'actual_end_date': fields.Date.today()
            })

    def action_reject_unassign(self):
        """Reject/Unassign worker - set back to available if not invoiced"""
        for placement in self:
            if placement.invoiced:
                raise UserError(_('Cannot reject/unassign worker for placement %s because it has already been invoiced.') % placement.name)
            job_order = placement.job_order_id
            placement.write({'state': 'cancelled'})
            # Force recompute positions on job order
            job_order._compute_fill_status()

    def action_cancel(self):
        """Cancel the placement"""
        for placement in self:
            if placement.state not in ['draft', 'assigned']:
                raise UserError(_('Only draft or assigned placements can be cancelled.'))
            placement.write({'state': 'cancelled'})


    def unlink(self):
        """Prevent deletion of placements in active or completed state"""
        for placement in self:
            if placement.state in ['active', 'completed']:
                raise ValidationError(_('Cannot delete placement %s in state %s. You can only cancel draft or assigned placements.') % (placement.name, placement.state))
            if placement.invoiced:
                raise ValidationError(_('Cannot delete invoiced placement %s.') % placement.name)
        return super().unlink()

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for placement in self:
            if placement.start_date and placement.end_date:
                if placement.end_date < placement.start_date:
                    raise ValidationError(_('End date cannot be before start date.'))

    @api.constrains('worker_id', 'start_date', 'end_date', 'state')
    def _check_worker_overlap(self):
        """Prevent overlapping placements for the same worker"""
        for placement in self:
            if placement.state in ['assigned', 'active'] and placement.start_date:
                domain = [
                    ('id', '!=', placement.id),
                    ('worker_id', '=', placement.worker_id.id),
                    ('state', 'in', ['assigned', 'active']),
                ]

                overlapping = self.search(domain)
                for other in overlapping:
                    if other.start_date and placement.start_date:
                        # Check for date overlap
                        if placement.end_date and other.end_date:
                            if not (placement.end_date < other.start_date or placement.start_date > other.end_date):
                                raise ValidationError(
                                    _('Worker %s already has an overlapping placement from %s to %s.') %
                                    (placement.worker_id.name, other.start_date, other.end_date)
                                )
