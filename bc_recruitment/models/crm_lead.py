# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # BC Recruitment fields
    is_bc_recruitment = fields.Boolean(string='Is BC Recruitment', default=False,
                                      help='Check if this lead is for blue collar recruitment')

    required_workers = fields.Integer(string='Required Workers', default=0)
    job_category = fields.Char(string='Job Category')
    work_location = fields.Char(string='Work Location')

    def action_new_quotation(self):
        """Override to set BC recruitment flag on sale order"""
        result = super().action_new_quotation()

        if self.is_bc_recruitment and result.get('res_id'):
            sale_order = self.env['sale.order'].browse(result['res_id'])
            sale_order.write({'is_bc_recruitment': True})

        return result

    def _prepare_opportunity_quotation_context(self):
        """Override to pass BC recruitment flag to quotation context"""
        quotation_context = super()._prepare_opportunity_quotation_context()
        if self.is_bc_recruitment:
            quotation_context['default_is_bc_recruitment'] = True
        return quotation_context
