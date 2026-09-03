# -*- coding: utf-8 -*-

import base64
from odoo import http, _
from odoo.http import request
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment


class WebsiteJobSeeker(WebsiteHrRecruitment):
    # Customize jobs per page - reduced to keep page shorter
    _jobs_per_page = 3  # Shows 3 jobs per page

    def sitemap_jobs(env, rule, qs):
        if not qs or qs.lower() in '/jobs':
            yield {'loc': '/jobs'}

    @http.route([
        '/jobs',
        '/jobs/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=sitemap_jobs)
    def jobs(self, page=1, department_id=None, contract_type_id=None, office_id=None, **kwargs):
        """Override jobs page to add filtering and form data"""
        # Call parent method with filtering parameters
        response = super(WebsiteJobSeeker, self).jobs(
            page=page,
            department_id=department_id,
            contract_type_id=contract_type_id,
            office_id=office_id,
            **kwargs
        )

        # Get filter options for dropdowns
        all_departments = request.env['hr.department'].sudo().search([])
        all_contract_types = request.env['hr.contract.type'].sudo().search([])
        degrees = request.env['hr.recruitment.degree'].sudo().search([])

        # Get unique offices/locations from published jobs
        jobs_with_location = request.env['hr.job'].sudo().search([
            ('website_published', '=', True),
            ('address_id', '!=', False)
        ])
        all_offices = jobs_with_location.mapped('address_id')

        # Add to context
        if hasattr(response, 'qcontext'):
            response.qcontext.update({
                'departments': degrees,  # For registration form
                'degrees': degrees,  # For registration form
                'all_departments': all_departments,  # For filtering
                'all_contract_types': all_contract_types,
                'all_offices': all_offices,
                'selected_department': int(department_id) if department_id else None,
                'selected_contract_type': int(contract_type_id) if contract_type_id else None,
                'selected_office': int(office_id) if office_id else None,
            })

        return response

    @http.route(['/jobs/detail/<model("hr.job"):job>'], type='http', auth="public", website=True, sitemap=True)
    def jobs_detail(self, job, **kwargs):
        """Show job detail page"""
        return super(WebsiteJobSeeker, self).jobs_detail(job, **kwargs)

    @http.route('/job-seeker/register', type='http', auth="public", website=True, methods=['POST'], csrf=True)
    def job_seeker_register(self, **post):
        """Handle job seeker registration form submission"""
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Extract form data
            vals = {
                'name': post.get('name', ''),
                'email': post.get('email', ''),
                'phone': post.get('phone', ''),
                'mobile': post.get('mobile', ''),
                'job_position': post.get('job_position', ''),
                'experience_years': int(post.get('experience_years', 0)) if post.get('experience_years') else 0,
                'expected_salary': float(post.get('expected_salary', 0)) if post.get('expected_salary') else 0,
                'availability_date': post.get('availability_date', False) or False,
                'cover_letter': post.get('cover_letter', ''),
            }

            # Handle department
            if post.get('department_id'):
                try:
                    dept_id = int(post.get('department_id'))
                    if dept_id > 0:
                        vals['department_id'] = dept_id
                except (ValueError, TypeError):
                    _logger.warning('Invalid department_id: %s', post.get('department_id'))

            # Handle degree
            if post.get('degree_id'):
                try:
                    degree_id = int(post.get('degree_id'))
                    if degree_id > 0:
                        vals['degree_id'] = degree_id
                except (ValueError, TypeError):
                    _logger.warning('Invalid degree_id: %s', post.get('degree_id'))

            # Handle resume file upload
            if post.get('resume'):
                resume_file = post.get('resume')
                if hasattr(resume_file, 'read'):
                    vals['resume'] = base64.b64encode(resume_file.read())
                    vals['resume_filename'] = resume_file.filename

            # Create the registration
            registration = request.env['job.seeker.registration'].sudo().create(vals)
            _logger.info('Job seeker registration created: ID=%s, Name=%s', registration.id, registration.name)

            # Redirect to thank you page
            return request.redirect('/job-seeker/thank-you')

        except Exception as e:
            # Log the error
            _logger.exception('Job Seeker Registration Error')

            return request.render('website.http_error', {
                'status_code': _('Error'),
                'status_message': _('Unable to process your registration. Please try again later or contact us directly.'),
            })

    @http.route('/job-seeker/thank-you', type='http', auth="public", website=True, sitemap=False)
    def job_seeker_thank_you(self, **kwargs):
        """Thank you page after registration"""
        return request.render('job_seeker_registration.job_seeker_thank_you')
