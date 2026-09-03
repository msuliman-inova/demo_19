# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # BC Recruitment fields
    is_bc_client = fields.Boolean(string='Is BC Client', default=False,
                                  help='Check if this partner is a blue collar recruitment client')
    is_customer = fields.Boolean(string='Is Customer', default=False,
                                 help='Check if this partner is a customer')
    is_agency = fields.Boolean(string='Is Agency', default=False,
                               help='Check if this partner is an agency')

    job_order_ids = fields.One2many('bc.job.order', 'partner_id', string='Job Orders')
    job_order_count = fields.Integer(string='Job Orders', compute='_compute_job_order_count', store=True)

    placement_ids = fields.One2many('bc.placement', 'partner_id', string='Placements')
    placement_count = fields.Integer(string='Placements', compute='_compute_placement_count', store=True)

    @api.depends('job_order_ids')
    def _compute_job_order_count(self):
        for partner in self:
            partner.job_order_count = len(partner.job_order_ids)

    @api.depends('placement_ids')
    def _compute_placement_count(self):
        for partner in self:
            partner.placement_count = len(partner.placement_ids)

    def action_view_job_orders(self):
        """View all job orders for this partner"""
        self.ensure_one()

        return {
            'name': _('Job Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'bc.job.order',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_placements(self):
        """View all placements for this partner"""
        self.ensure_one()

        return {
            'name': _('Placements'),
            'type': 'ir.actions.act_window',
            'res_model': 'bc.placement',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }
