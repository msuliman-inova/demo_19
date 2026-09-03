from odoo import api, fields, models, _


class HrJob(models.Model):
    _inherit = 'hr.job'

    recruitment_request_id = fields.Many2one(
        'recruitment.request',
        string='Recruitment Request',
        readonly=True
    )

    job_type = fields.Selection([
        ('internal', 'Internal Job'),
        ('external', 'External Job (Client)'),
    ], string='Job Type', default='internal', required=True, tracking=True,
        help="Internal: Job for your own company\nExternal: Job for client companies (recruitment services)")

    partner_id = fields.Many2one(
        'res.partner',
        string='Client Company',
        store=True,
        tracking=True,
        help="The client company for whom this job is being recruited (for external jobs)"
    )

    is_external_recruitment = fields.Boolean(
        string='External Recruitment',
        compute='_compute_is_external_recruitment',
        store=True
    )

    @api.depends('recruitment_request_id', 'job_type')
    def _compute_is_external_recruitment(self):
        for job in self:
            job.is_external_recruitment = bool(job.recruitment_request_id) or job.job_type == 'external'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to link job with recruitment request and set client company"""
        # Set partner_id from recruitment_request if not already set
        for vals in vals_list:
            if vals.get('recruitment_request_id') and not vals.get('partner_id'):
                recruitment_request = self.env['recruitment.request'].browse(vals['recruitment_request_id'])
                vals['partner_id'] = recruitment_request.partner_id.id

        jobs = super(HrJob, self).create(vals_list)

        for job in jobs:
            if job.recruitment_request_id:
                # Update recruitment request state if needed
                if job.recruitment_request_id.state == 'approved':
                    job.recruitment_request_id.state = 'in_progress'

                # Post message on recruitment request
                job.recruitment_request_id.message_post(
                    body=_('Job position created: <a href="#" data-oe-model="hr.job" data-oe-id="%d">%s</a>') % (job.id, job.name),
                    subject=_('Job Position Created')
                )

        return jobs

    def action_view_recruitment_request(self):
        """View related recruitment request"""
        self.ensure_one()
        return {
            'name': _('Recruitment Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'recruitment.request',
            'view_mode': 'form',
            'res_id': self.recruitment_request_id.id,
        }


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    recruitment_request_id = fields.Many2one(
        'recruitment.request',
        related='job_id.recruitment_request_id',
        string='Recruitment Request',
        store=True,
        readonly=True
    )

    client_company_id = fields.Many2one(
        'res.partner',
        related='job_id.partner_id',
        string='Client Company',
        store=True,
        readonly=True
    )
