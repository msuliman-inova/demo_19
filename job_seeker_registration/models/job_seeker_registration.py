# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class JobSeekerRegistration(models.Model):
    _name = 'job.seeker.registration'
    _description = 'Job Seeker Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Applicant Name', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    mobile = fields.Char(string='Mobile')

    partner_id = fields.Many2one('res.partner', string='Contact')

    # Job related fields
    job_position = fields.Char(string='Desired Position', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    expected_salary = fields.Float(string='Expected Salary')
    availability_date = fields.Date(string='Available From')

    # Additional information
    degree_id = fields.Many2one('hr.recruitment.degree', string='Degree')
    experience_years = fields.Integer(string='Years of Experience')
    resume = fields.Binary(string='Resume/CV', attachment=True)
    resume_filename = fields.Char(string='Resume Filename')
    cover_letter = fields.Text(string='Cover Letter')

    # Status and tracking
    state = fields.Selection([
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('interested', 'Still Interested'),
        ('not_interested', 'Not Interested'),
        ('converted', 'Converted to Application'),
        ('archived', 'Archived'),
    ], string='Status', default='new', required=True, tracking=True)

    application_id = fields.Many2one('hr.applicant', string='Job Application', readonly=True, tracking=True)
    converted_date = fields.Datetime(string='Conversion Date', readonly=True)

    notes = fields.Text(string='Internal Notes')
    active = fields.Boolean(string='Active', default=True)

    # Computed fields
    application_count = fields.Integer(compute='_compute_application_count', string='Applications')

    @api.depends('application_id')
    def _compute_application_count(self):
        for record in self:
            record.application_count = 1 if record.application_id else 0

    def action_contact_seeker(self):
        """Mark as contacted"""
        self.write({'state': 'contacted'})
        return True

    def action_mark_interested(self):
        """Mark as still interested"""
        self.write({'state': 'interested'})
        return True

    def action_mark_not_interested(self):
        """Mark as not interested"""
        self.write({'state': 'not_interested'})
        return True

    def action_archive(self):
        """Archive the registration"""
        self.write({'state': 'archived', 'active': False})
        return True

    def action_convert_to_application(self):
        """Open wizard to convert job seeker registration to job application"""
        self.ensure_one()

        if self.application_id:
            raise UserError(_('This registration has already been converted to an application.'))

        return {
            'name': _('Convert to Application'),
            'type': 'ir.actions.act_window',
            'res_model': 'job.seeker.convert.wizard',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'is_modal': True,
                'dialog_size': 'medium',
                'default_seeker_id': self.id,
            },
        }

    def action_view_application(self):
        """View the converted job application"""
        self.ensure_one()
        if not self.application_id:
            raise UserError(_('No application has been created yet.'))

        return {
            'name': _('Job Application'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'view_mode': 'form',
            'res_id': self.application_id.id,
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Create partner if email provided and partner not exists"""
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('email') and not vals.get('partner_id'):
                partner = self.env['res.partner'].search([('email', '=', vals['email'])], limit=1)
                if partner:
                    vals['partner_id'] = partner.id

        return super(JobSeekerRegistration, self).create(vals_list)
