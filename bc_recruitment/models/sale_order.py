# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # BC Recruitment fields
    is_bc_recruitment = fields.Boolean(string='Is BC Recruitment', default=False, copy=False)
    job_order_ids = fields.One2many('bc.job.order', 'sale_order_id', string='Job Orders')
    job_order_count = fields.Integer(string='Job Orders', compute='_compute_job_order_count', store=True)

    # Partner type flags (related fields for easy access in views)
    partner_is_customer = fields.Boolean(string='Partner Is Customer', related='partner_id.is_customer', readonly=True)
    partner_is_agency = fields.Boolean(string='Partner Is Agency', related='partner_id.is_agency', readonly=True)

    @api.model
    def create(self, vals):
        """Auto-set BC recruitment flag from opportunity"""
        # If created from opportunity, check if it's BC recruitment
        if 'opportunity_id' in vals and vals.get('opportunity_id'):
            opportunity = self.env['crm.lead'].browse(vals['opportunity_id'])
            if opportunity.is_bc_recruitment:
                vals['is_bc_recruitment'] = True

        return super().create(vals)

    @api.depends('job_order_ids')
    def _compute_job_order_count(self):
        for order in self:
            order.job_order_count = len(order.job_order_ids)

    def action_confirm(self):
        """Override to auto-create job orders for BC recruitment sales"""
        result = super().action_confirm()

        for order in self:
            if order.is_bc_recruitment and not order.job_order_ids:
                order._create_job_orders_from_sale_order()

        return result

    def _create_job_orders_from_sale_order(self):
        """Create job orders from sale order lines"""
        self.ensure_one()

        job_order_obj = self.env['bc.job.order']

        for line in self.order_line:
            # Skip lines without product or service lines
            if not line.product_id or line.display_type:
                continue

            # Create job order from sale order line
            job_order_vals = {
                'sale_order_id': self.id,
                'sale_line_id': line.id,  # Link to specific sale order line
                'partner_id': self.partner_id.id,
                'job_title': line.name or line.product_id.name,
                'job_description': line.name,
                'positions_requested': int(line.product_uom_qty) if line.product_uom_qty > 0 else 1,
                'work_location': self.partner_shipping_id.city or '',
                'country_id': self.partner_shipping_id.country_id.id if self.partner_shipping_id.country_id else False,
                'currency_id': self.currency_id.id,
                'placement_fee': line.price_unit,  # Fee per placement
                'state': 'confirmed',
                'user_id': self.user_id.id if self.user_id else self.env.user.id,
            }

            job_order_obj.create(job_order_vals)

    def unlink(self):
        """Prevent deletion of BC recruitment sale orders with job orders"""
        for order in self:
            if order.is_bc_recruitment and order.job_order_ids:
                raise ValidationError(_('Cannot delete BC Recruitment sale order %s with existing job orders.') % order.name)
        return super().unlink()

    def action_view_job_orders(self):
        """View job orders related to this sale order"""
        self.ensure_one()

        return {
            'name': _('Job Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'bc.job.order',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id, 'default_partner_id': self.partner_id.id}
        }

    def action_bc_dashboard(self):
        """Open BC Recruitment Dashboard"""
        self.ensure_one()

        return {
            'name': _('BC Recruitment Dashboard'),
            'type': 'ir.actions.act_window',
            'res_model': 'bc.dashboard.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            }
        }
