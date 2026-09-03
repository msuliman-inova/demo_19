# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class JobSeekerConvertWizard(models.TransientModel):
    _name = 'job.seeker.convert.wizard'
    _description = 'Convert Job Seeker to Application'

    seeker_id = fields.Many2one('job.seeker.registration', string='Job Seeker', required=True, ondelete='cascade')
    job_id = fields.Many2one('hr.job', string='Job Position', required=True)
    department_id = fields.Many2one('hr.department', string='Department', related='job_id.department_id', readonly=True)

    # Display seeker info
    seeker_name = fields.Char(related='seeker_id.name', readonly=True)
    seeker_email = fields.Char(related='seeker_id.email', readonly=True)
    seeker_phone = fields.Char(related='seeker_id.phone', readonly=True)
    seeker_position = fields.Char(related='seeker_id.job_position', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super(JobSeekerConvertWizard, self).default_get(fields_list)

        seeker_id = self.env.context.get('active_id')
        if seeker_id:
            seeker = self.env['job.seeker.registration'].browse(seeker_id)
            res['seeker_id'] = seeker_id

            # Try to find matching job
            if seeker.job_position:
                job = self.env['hr.job'].search([
                    ('name', 'ilike', seeker.job_position)
                ], limit=1)
                if job:
                    res['job_id'] = job.id

        return res

    def action_convert(self):
        """Convert job seeker to application"""
        self.ensure_one()

        if self.seeker_id.application_id:
            raise UserError(_('This registration has already been converted to an application.'))

        # Create partner if email exists and no partner linked
        partner_id = self.seeker_id.partner_id.id if self.seeker_id.partner_id else False
        if self.seeker_id.email and not partner_id:
            partner = self.env['res.partner'].search([('email', '=', self.seeker_id.email)], limit=1)
            if partner:
                partner_id = partner.id
                self.seeker_id.partner_id = partner

        # Prepare application values
        applicant_vals = {
            'partner_name': self.seeker_id.name,
            'email_from': self.seeker_id.email,
            'partner_phone': self.seeker_id.phone or self.seeker_id.mobile,
            'partner_id': partner_id,
            'job_id': self.job_id.id,
            'department_id': self.job_id.department_id.id if self.job_id.department_id else False,
            'salary_expected': self.seeker_id.expected_salary,
            'availability': self.seeker_id.availability_date,
            'applicant_notes': self.seeker_id.cover_letter or '',
        }

        # Get initial recruitment stage
        stage = self.env['hr.recruitment.stage'].search([('fold', '=', False)], order='sequence', limit=1)
        if stage:
            applicant_vals['stage_id'] = stage.id

        # Create the application
        applicant = self.env['hr.applicant'].create(applicant_vals)

        # Attach resume if exists
        if self.seeker_id.resume:
            self.env['ir.attachment'].create({
                'name': self.seeker_id.resume_filename or 'Resume.pdf',
                'datas': self.seeker_id.resume,
                'res_model': 'hr.applicant',
                'res_id': applicant.id,
                'type': 'binary',
            })

        # Update seeker registration
        self.seeker_id.write({
            'application_id': applicant.id,
            'state': 'converted',
            'converted_date': fields.Datetime.now(),
        })

        # Post a message on the applicant
        applicant.message_post(
            body=_('This application was created from a job seeker registration.'),
            message_type='notification',
        )

        # Return action to view the created application
        return {
            'name': _('Job Application'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'view_mode': 'form',
            'res_id': applicant.id,
            'target': 'current',
        }
