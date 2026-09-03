# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BCJobOrder(models.Model):
    _name = 'bc.job.order'
    _description = 'Blue Collar Job Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    # Basic Information
    name = fields.Char(string='Job Order Number', required=True, copy=False, readonly=True,
                      default=lambda self: _('New'), tracking=True)

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True,
                                   ondelete='cascade', tracking=True)
    sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line',
                                   ondelete='cascade', tracking=True,
                                   help='Specific sale order line this job order is for')
    partner_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)

    # Computed fields for display
    sale_order_display = fields.Char(string='Sale Order Info', compute='_compute_sale_order_display', store=True)
    product_id = fields.Many2one('product.product', string='Product', related='sale_line_id.product_id', store=True)

    # Job Details
    job_title = fields.Char(string='Job Title', required=True, tracking=True)
    job_description = fields.Text(string='Job Description')

    skill_ids = fields.Many2many('bc.worker.skill', string='Required Skills')

    positions_requested = fields.Integer(string='Positions Requested', required=True, default=1, tracking=True)
    positions_filled = fields.Integer(string='Positions Filled', compute='_compute_fill_status', store=True)
    positions_remaining = fields.Integer(string='Positions Remaining', compute='_compute_fill_status', store=True)
    fill_rate = fields.Float(string='Fill Rate (%)', compute='_compute_fill_status', store=True)

    # Location & Schedule
    work_location = fields.Char(string='Work Location', required=True)
    country_id = fields.Many2one('res.country', string='Country')

    contract_type = fields.Selection([
        ('permanent', 'Permanent'),
        ('temporary', 'Temporary'),
        ('contract', 'Contract'),
        ('seasonal', 'Seasonal')
    ], string='Contract Type', default='contract', required=True)

    expected_start_date = fields.Date(string='Expected Start Date', tracking=True)
    contract_duration_months = fields.Integer(string='Contract Duration (Months)')

    # Salary & Benefits
    salary_from = fields.Monetary(string='Salary From', currency_field='currency_id')
    salary_to = fields.Monetary(string='Salary To', currency_field='currency_id')
    placement_fee = fields.Monetary(string='Placement Fee (per worker)', currency_field='currency_id',
                                   help='Fee charged to client per worker placement')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    benefits = fields.Text(string='Benefits')

    # Placements
    placement_ids = fields.One2many('bc.placement', 'job_order_id', string='Placements')
    placement_count = fields.Integer(string='Placements', compute='_compute_placement_count', store=True)

    # Status & Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True, copy=False,
        group_expand='_group_expand_states')

    @api.model
    def _group_expand_states(self, states, domain):
        return ['draft', 'confirmed', 'in_progress', 'completed', 'cancelled']

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)

    # Dates
    deadline = fields.Date(string='Deadline', tracking=True)
    completion_date = fields.Date(string='Completion Date', readonly=True, tracking=True)

    # Other
    notes = fields.Text(string='Internal Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)

    @api.depends('sale_order_id', 'sale_line_id', 'partner_id')
    def _compute_sale_order_display(self):
        for order in self:
            if order.sale_line_id:
                order.sale_order_display = f"{order.sale_order_id.name} - {order.partner_id.name} - Line: {order.sale_line_id.name}"
            elif order.sale_order_id:
                order.sale_order_display = f"{order.sale_order_id.name} - {order.partner_id.name}"
            else:
                order.sale_order_display = ""

    @api.depends('placement_ids', 'placement_ids.state')
    def _compute_placement_count(self):
        for order in self:
            order.placement_count = len(order.placement_ids)

    @api.depends('positions_requested', 'placement_ids', 'placement_ids.state')
    def _compute_fill_status(self):
        for order in self:
            filled = len(order.placement_ids.filtered(lambda p: p.state in ['assigned', 'active', 'completed']))
            order.positions_filled = filled
            order.positions_remaining = order.positions_requested - filled
            order.fill_rate = (filled / order.positions_requested * 100) if order.positions_requested > 0 else 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bc.job.order') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """Update state to completed when all positions are filled"""
        result = super().write(vals)
        for order in self:
            if order.state == 'in_progress' and order.positions_filled >= order.positions_requested:
                order.state = 'completed'
                order.completion_date = fields.Date.today()
        return result

    def action_confirm(self):
        """Confirm the job order"""
        for order in self:
            if order.state == 'draft':
                order.write({'state': 'confirmed'})

    def action_start(self):
        """Start processing the job order"""
        for order in self:
            if order.state == 'confirmed':
                order.write({'state': 'in_progress'})

    def action_complete(self):
        """Mark job order as completed"""
        self.ensure_one()

        # If positions are not fully filled, show confirmation wizard
        if self.positions_filled < self.positions_requested:
            return {
                'name': _('Confirm Job Order Completion'),
                'type': 'ir.actions.act_window',
                'res_model': 'job.order.complete.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_job_order_id': self.id,
                }
            }

        # All positions filled, complete directly
        self.write({
            'state': 'completed',
            'completion_date': fields.Date.today()
        })

    def action_cancel(self):
        """Cancel the job order"""
        for order in self:
            active_placements = order.placement_ids.filtered(lambda p: p.state in ['assigned', 'active'])
            if active_placements:
                raise UserError(_('Cannot cancel job order with active placements. Please terminate placements first.'))
            order.write({'state': 'cancelled'})

    def action_reset_to_in_progress(self):
        """Reset job order from completed back to in progress"""
        for order in self:
            if order.state != 'completed':
                raise UserError(_('Only completed job orders can be reset to in progress.'))
            order.write({
                'state': 'in_progress',
                'completion_date': False
            })

    def action_view_placements(self):
        """View all placements for this job order"""
        self.ensure_one()
        return {
            'name': _('Job Order Placements'),
            'type': 'ir.actions.act_window',
            'res_model': 'bc.placement',
            'view_mode': 'list,form',
            'domain': [('job_order_id', '=', self.id)],
            'context': {'default_job_order_id': self.id}
        }

    def action_create_placement(self):
        """Create new placement for this job order"""
        self.ensure_one()
        if self.positions_remaining <= 0:
            raise UserError(_('All positions for this job order are already filled.'))

        return {
            'name': _('Create Placement'),
            'type': 'ir.actions.act_window',
            'res_model': 'bc.placement',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_job_order_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
        }

    def action_view_sale_order(self):
        """View related sale order"""
        self.ensure_one()
        return {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def unlink(self):
        """Prevent deletion of job orders with placements or in progress"""
        for order in self:
            if order.state in ['in_progress', 'completed']:
                raise ValidationError(_('Cannot delete job order %s in state %s. Cancel it first.') % (order.name, order.state))
            if order.placement_ids:
                raise ValidationError(_('Cannot delete job order %s with existing placements.') % order.name)
        return super().unlink()

    @api.constrains('positions_requested')
    def _check_positions_requested(self):
        for order in self:
            if order.positions_requested <= 0:
                raise ValidationError(_('Positions requested must be greater than zero.'))

    def action_create_bulk_invoices(self):
        """Create single invoice for all non-invoiced active/completed placements"""
        self.ensure_one()

        # Get placements that can be invoiced
        placements_to_invoice = self.placement_ids.filtered(
            lambda p: not p.invoiced and p.state in ['active', 'completed']
        )

        if not placements_to_invoice:
            raise UserError(_('No placements available for invoicing. All placements are either already invoiced or not in active/completed state.'))

        if not self.sale_line_id:
            raise UserError(_('No sale order line linked to this job order. Cannot create invoice.'))

        # Create single invoice for all placements
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.sale_order_id.name,
            'ref': self.name,
            'invoice_line_ids': [(0, 0, {
                'name': _('%s - %d Workers Placed') % (self.sale_line_id.name, len(placements_to_invoice)),
                'quantity': len(placements_to_invoice),
                'price_unit': self.sale_line_id.price_unit,
                'product_id': self.product_id.id if self.product_id else False,
                'sale_line_ids': [(6, 0, [self.sale_line_id.id])],
            })]
        }

        invoice = self.env['account.move'].create(invoice_vals)

        # Mark all placements as invoiced and link to invoice
        placements_to_invoice.write({
            'invoiced': True,
            'invoice_id': invoice.id
        })

        # Return action to view created invoice
        return {
            'name': _('Invoice Created'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
