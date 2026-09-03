# -*- coding: utf-8 -*-

from odoo import fields, models


class RecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    # hired_stage = fields.Boolean(
    #     string='Hired Stage',
    #     default=False,
    #     help='Check this box if this stage represents a hired applicant'
    # )
    # Note: hired_stage is already available in Odoo 19 base hr_recruitment module

    visible_to_client = fields.Boolean(
        string='Visible to Client',
        default=True,
        help='If checked, applicants in this stage will be visible to the client on the portal'
    )
