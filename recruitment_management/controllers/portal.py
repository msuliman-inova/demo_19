from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, route
from markupsafe import Markup
import re

class RecruitmentPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'recruitment_count' in counters:
            partner = request.env.user.partner_id
            recruitment_count = request.env['recruitment.request'].search_count([
                ('partner_id', '=', partner.commercial_partner_id.id)
            ])
            values['recruitment_count'] = recruitment_count
        return values

    def _get_recruitment_searchbar_sortings(self):
        return {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Reference'), 'order': 'name desc, id desc'},
            'state': {'label': _('Status'), 'order': 'state, create_date desc'},
        }

    def _get_recruitment_searchbar_filters(self):
        return {
            'all': {'label': _('All'), 'domain': []},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'submitted': {'label': _('Submitted'), 'domain': [('state', '=', 'submitted')]},
            'under_review': {'label': _('Under Review'), 'domain': [('state', '=', 'under_review')]},
            'quotation_sent': {'label': _('Quotation Sent'), 'domain': [('state', '=', 'quotation_sent')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'approved')]},
            'in_progress': {'label': _('In Progress'), 'domain': [('state', '=', 'in_progress')]},
            'completed': {'label': _('Completed'), 'domain': [('state', '=', 'completed')]},
        }

    def _recruitment_request_get_page_view_values(self, recruitment_request, access_token, **kwargs):
        values = {
            'page_name': 'recruitment_request',
            'recruitment_request': recruitment_request,
        }
        return self._get_page_view_values(recruitment_request, access_token, values, 'my_recruitment_history', False,
                                          **kwargs)

    @route(['/my/recruitment', '/my/recruitment/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_recruitment_requests(self, page=1, sortby=None, filterby=None, search=None, **kw):
        values = self._prepare_portal_layout_values()
        RecruitmentRequest = request.env['recruitment.request']
        partner = request.env.user.partner_id
        domain = [('partner_id', '=', partner.commercial_partner_id.id)]

        searchbar_sortings = self._get_recruitment_searchbar_sortings()
        searchbar_filters = self._get_recruitment_searchbar_filters()

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if search:
            domain += [
                '|', '|',
                ('name', 'ilike', search),
                ('work_location', 'ilike', search),
                ('partner_id.name', 'ilike', search)
            ]

        recruitment_count = RecruitmentRequest.search_count(domain)

        pager = portal_pager(
            url="/my/recruitment",
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=recruitment_count,
            page=page,
            step=self._items_per_page
        )

        requests = RecruitmentRequest.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        # Calculate status counts for dashboard
        base_domain = [('partner_id', '=', partner.commercial_partner_id.id)]
        status_counts = {
            'draft': RecruitmentRequest.search_count(base_domain + [('state', '=', 'draft')]),
            'submitted': RecruitmentRequest.search_count(base_domain + [('state', '=', 'submitted')]),
            'under_review': RecruitmentRequest.search_count(base_domain + [('state', '=', 'under_review')]),
            'quotation_sent': RecruitmentRequest.search_count(base_domain + [('state', '=', 'quotation_sent')]),
            'approved': RecruitmentRequest.search_count(base_domain + [('state', '=', 'approved')]),
            'in_progress': RecruitmentRequest.search_count(base_domain + [('state', '=', 'in_progress')]),
            'completed': RecruitmentRequest.search_count(base_domain + [('state', '=', 'completed')]),
        }

        # Calculate urgency metrics across all recruitment requests
        all_requests = RecruitmentRequest.sudo().search(base_domain)
        all_job_ids = all_requests.mapped('line_ids.job_id').ids
        all_applicants = request.env['hr.applicant'].sudo().search([
            ('job_id', 'in', all_job_ids)
        ])

        # Build a dictionary of requests with urgent/attention applicants
        urgent_requests = []
        attention_requests = []

        for req in all_requests:
            req_job_ids = req.line_ids.mapped('job_id').ids
            req_applicants = all_applicants.filtered(lambda a: a.job_id.id in req_job_ids)

            urgent_count = len(req_applicants.filtered(lambda a: a.urgency_status in ['urgent', 'overdue']))
            attention_count = len(req_applicants.filtered(lambda a: a.urgency_status == 'attention'))

            if urgent_count > 0:
                urgent_requests.append({
                    'request': req,
                    'count': urgent_count
                })
            if attention_count > 0:
                attention_requests.append({
                    'request': req,
                    'count': attention_count
                })

        values.update({
            'requests': requests,
            'page_name': 'recruitment',
            'pager': pager,
            'default_url': '/my/recruitment',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'search': search,
            'status_counts': status_counts,
            'urgent_requests': urgent_requests,
            'attention_requests': attention_requests,
        })
        return request.render("recruitment_management.portal_my_recruitment_requests", values)

    @route(['/my/recruitment/<int:request_id>'], type='http', auth="user", website=True)
    def portal_my_recruitment_request(self, request_id=None, access_token=None, **kw):
        try:
            recruitment_request_sudo = self._document_check_access('recruitment.request', request_id, access_token).sudo()
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._recruitment_request_get_page_view_values(recruitment_request_sudo, access_token, **kw)

        # Add contract types to the view context
        values['emp_contract_type'] = request.env['hr.contract.type'].sudo().search([])

        return request.render("recruitment_management.portal_my_recruitment_request", values)

    @route(['/my/recruitment/new'], type='http', auth="user", website=True)
    def portal_create_recruitment_request(self, mode='quick', **kw):
        """
        Create recruitment request - supports both quick and detailed modes
        mode: 'quick' for simple form (default), 'detailed' for full form
        """
        # Check if detailed mode is requested
        if mode == 'detailed':
            emp_contract_type = request.env['hr.contract.type'].sudo().search([])
            degrees = request.env['hr.recruitment.degree'].sudo().search([])
            skill_types = request.env['hr.skill.type'].sudo().search([('active', '=', True)])
            departments = request.env['hr.department'].sudo().search([])

            values = {
                'page_name': 'create_recruitment',
                'emp_contract_type': emp_contract_type,
                'degrees': degrees,
                'skill_types': skill_types,
                'departments': departments,
            }
            return request.render("recruitment_management.portal_create_recruitment_request", values)

        # Default: quick mode
        return request.render("recruitment_management.portal_quick_recruitment_request", {
            'page_name': 'quick_create_recruitment',
        })

    @route(['/my/recruitment/quick-create'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_quick_create_recruitment_request(self, **post):
        """Handle quick submit form submission - creates request and CRM lead without job lines"""
        import logging
        _logger = logging.getLogger(__name__)

        partner = request.env.user.partner_id

        # Get form data
        work_location = post.get('work_location')
        description = post.get('description')
        expected_start_date = post.get('expected_start_date') or False
        remote_work = bool(post.get('remote_work'))

        if not work_location or not description:
            return request.render('recruitment_management.portal_quick_recruitment_request', {
                'error': 'Work location and description are required.',
                'page_name': 'quick_create_recruitment',
            })

        # Create recruitment request WITHOUT job lines
        # Job description is stored in internal_notes for the recruitment team to process
        values = {
            'partner_id': partner.commercial_partner_id.id,
            'contact_person_id': partner.id if partner.parent_id else False,
            'work_location': work_location,
            'remote_work': remote_work,
            'expected_start_date': expected_start_date,
            'internal_notes': description,  # Store description in internal notes
            'is_portal_request': True,
            'state': 'submitted',  # Move to submitted state
            'submission_date': fields.Datetime.now(),
        }

        recruitment_request = request.env['recruitment.request'].sudo().create(values)
        _logger.info(f"Created quick recruitment request (no job lines): {recruitment_request.id}")

        # Create CRM Lead for the recruitment team to follow up
        lead_vals = {
            'name': f'Quick Recruitment Request: {partner.commercial_partner_id.name}',
            'partner_id': partner.commercial_partner_id.id,
            'contact_name': partner.name if partner.parent_id else False,
            'email_from': partner.email,
            'phone': partner.phone,
            'user_id': False,  # Unassigned - will be assigned by recruitment team
            'team_id': request.env.ref('recruitment_management.recruitment_sales_team',
                                      raise_if_not_found=False).id if request.env.ref(
                'recruitment_management.recruitment_sales_team', raise_if_not_found=False) else False,
            'type': 'opportunity',
            'description': f"""
                <p><strong>Quick Recruitment Request</strong></p>
                <p><strong>Location:</strong> {work_location}</p>
                <p><strong>Remote Work:</strong> {'Yes' if remote_work else 'No'}</p>
                {f'<p><strong>Expected Start Date:</strong> {expected_start_date}</p>' if expected_start_date else ''}
                <hr/>
                <p><strong>Requirements:</strong></p>
                <p>{description.replace(chr(10), '<br/>')}</p>
                <hr/>
                <p><em>This is a quick submit request. Please contact the client to gather detailed job requirements.</em></p>
            """,
            'recruitment_request_id': recruitment_request.id,
        }

        lead = request.env['crm.lead'].sudo().create(lead_vals)

        # Link the lead to the recruitment request
        recruitment_request.sudo().write({
            'lead_id': lead.id,
            'user_id': request.env.ref('base.public_user').id,
        })

        _logger.info(f"Created CRM lead {lead.id} for quick recruitment request {recruitment_request.id}")

        # Send notification email if template exists
        template = request.env.ref('recruitment_management.email_template_request_submitted', raise_if_not_found=False)
        if template:
            try:
                template.sudo().send_mail(recruitment_request.id, force_send=True)
            except Exception as e:
                _logger.warning(f"Failed to send notification email: {e}")

        # Log message on the recruitment request
        recruitment_request.message_post(
            body=_('Quick recruitment request submitted and CRM lead created. Waiting for recruitment team to add job position details.'),
            subject=_('Quick Request Submitted')
        )

        return request.redirect(f'/my/recruitment/{recruitment_request.id}')

    @route(['/my/recruitment/create'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_create_recruitment_request_submit(self, **post):
        import logging
        _logger = logging.getLogger(__name__)

        partner = request.env.user.partner_id

        # Debug: Log all POST data
        _logger.info("=== Portal Create Recruitment Request ===")
        _logger.info(f"POST keys: {list(post.keys())}")

        # Parse multiple job lines from job_lines[index][field] format
        job_lines_data = []
        job_indices = set()

        # Extract all job line indices from the form data
        for key in post.keys():
            if key.startswith('job_lines[') and '][' in key:
                # Extract index from job_lines[INDEX][field]
                index_str = key.split('[')[1].split(']')[0]
                try:
                    job_indices.add(int(index_str))
                except ValueError:
                    continue

        _logger.info(f"Found job indices: {sorted(job_indices)}")

        # Build job line data for each index
        for index in sorted(job_indices):
            # Parse skill_ids for this job line
            skill_ids_str = post.get(f'job_lines[{index}][job_skill_ids]', '')
            skill_ids = [int(i) for i in skill_ids_str.split(',') if i.strip()]

            # Get required fields
            job_title = post.get(f'job_lines[{index}][job_title]', '').strip()
            emp_contract_type = post.get(f'job_lines[{index}][emp_contract_type]', '').strip()
            job_description = post.get(f'job_lines[{index}][job_description]', '').strip()

            _logger.info(f"Job {index}: title='{job_title}', contract_type='{emp_contract_type}', desc_len={len(job_description)}")

            # Skip lines with missing required fields
            if not job_title or not emp_contract_type or not job_description:
                _logger.warning(f"Skipping job {index} - missing required fields")
                continue

            line_data = {
                'job_title': job_title,
                'department_id': int(post.get(f'job_lines[{index}][department_id]')) if post.get(f'job_lines[{index}][department_id]') else False,
                'no_of_positions': int(post.get(f'job_lines[{index}][no_of_positions]', 1)),
                'job_description': job_description,
                'requirements': post.get(f'job_lines[{index}][requirements]', ''),
                'experience_years': int(post.get(f'job_lines[{index}][experience_years]', 0)),
                'emp_contract_type': int(emp_contract_type),
                'expected_degree': int(post.get(f'job_lines[{index}][expected_degree]')) if post.get(f'job_lines[{index}][expected_degree]') else False,
                'job_skill_ids': [(6, 0, skill_ids)],
            }

            if post.get(f'job_lines[{index}][salary_from]'):
                line_data['salary_from'] = float(post.get(f'job_lines[{index}][salary_from]'))
            if post.get(f'job_lines[{index}][salary_to]'):
                line_data['salary_to'] = float(post.get(f'job_lines[{index}][salary_to]'))

            job_lines_data.append((0, 0, line_data))
            _logger.info(f"Added job line {index} to creation list")

        _logger.info(f"Total job lines to create: {len(job_lines_data)}")

        if not job_lines_data:
            _logger.error("No valid job lines found!")
            # Return error to user
            return request.render('recruitment_management.portal_create_recruitment_request', {
                'error': 'Please fill in all required fields for at least one job position.',
                'emp_contract_type': request.env['hr.contract.type'].sudo().search([]),
                'degrees': request.env['hr.recruitment.degree'].sudo().search([]),
                'skill_types': request.env['hr.skill.type'].sudo().search([('active', '=', True)]),
                'departments': request.env['hr.department'].sudo().search([]),
            })

        # Create recruitment request with multiple job lines
        values = {
            'partner_id': partner.commercial_partner_id.id,
            'contact_person_id': partner.id if partner.parent_id else False,
            'work_location': post.get('work_location'),
            'remote_work': bool(post.get('remote_work')),
            'benefits': post.get('benefits'),
            'expected_start_date': post.get('expected_start_date') or False,
            'line_ids': job_lines_data,
            'is_portal_request': True,  # Mark as portal request (external)
            'user_id': request.env.ref('base.public_user').id,  # Assign to public user
        }

        recruitment_request = request.env['recruitment.request'].sudo().create(values)
        _logger.info(f"Created recruitment request: {recruitment_request.id}")

        if post.get('button_submit'):
            recruitment_request.action_submit()

        return request.redirect(f'/my/recruitment/{recruitment_request.id}')

    @route(['/my/recruitment/<int:request_id>/submit'], type='http', auth="user", website=True)
    def portal_submit_recruitment_request(self, request_id, **kw):
        try:
            recruitment_request_sudo = self._document_check_access('recruitment.request', request_id).sudo()
        except (AccessError, MissingError):
            return request.redirect('/my')

        if recruitment_request_sudo.state == 'draft':
            # Check if request has job lines - required for submission
            if not recruitment_request_sudo.line_ids:
                # Quick submit request without job lines - cannot be submitted from portal
                recruitment_request_sudo.message_post(
                    body=_('Request cannot be submitted without job position details. Our recruitment team will review your request and contact you shortly.'),
                    subject=_('Submission Pending'),
                    message_type='notification'
                )
                return request.redirect(f'/my/recruitment/{request_id}?error=no_job_lines')

            recruitment_request_sudo.action_submit()

        return request.redirect(f'/my/recruitment/{request_id}')

    def _clean_html(self, html_text):
        """Remove HTML tags from text"""
        if not html_text:
            return ''
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_text)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text.strip()

    @route(['/my/recruitment/<int:request_id>/edit'], type='http', auth="user", website=True)
    def portal_edit_recruitment_request(self, request_id=None, **kw):
        try:
            recruitment_request = self._document_check_access('recruitment.request', request_id).sudo()
        except (AccessError, MissingError):
            return request.redirect('/my')

        allowed_states = ['draft', 'submitted', 'under_review', 'quotation_sent']
        if request.env.user.partner_id.user_type != 'employer' or recruitment_request.state not in allowed_states:
            return request.redirect('/my/recruitment')

        # Prepare cleaned text for HTML fields
        lines_cleaned = []
        for line in recruitment_request.line_ids:
            line_dict = {
                'id': line.id,
                'job_title': line.job_title,
                'no_of_positions': line.no_of_positions,
                'experience_years': line.experience_years,
                'salary_from': line.salary_from,
                'salary_to': line.salary_to,
                'pricing_percentage': line.pricing_percentage,
                'department_id': line.department_id,
                'emp_contract_type': line.emp_contract_type,
                'job_description': self._clean_html(line.job_description),
                'requirements': self._clean_html(line.requirements),
            }
            lines_cleaned.append(line_dict)

        emp_contract_type = request.env['hr.contract.type'].sudo().search([])
        degrees = request.env['hr.recruitment.degree'].sudo().search([])
        skill_types = request.env['hr.skill.type'].sudo().search([('active', '=', True)])
        departments = request.env['hr.department'].sudo().search([])

        values = {
            'page_name': 'edit_recruitment',
            'recruitment_request': recruitment_request,
            'lines_cleaned': lines_cleaned,
            'emp_contract_type': emp_contract_type,
            'degrees': degrees,
            'skill_types': skill_types,
            'departments': departments,
        }
        return request.render("recruitment_management.portal_edit_recruitment_request", values)

    @route(['/my/recruitment/update'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_update_recruitment_request(self, **post):
        request_id = int(post.get('request_id'))
        try:
            recruitment_request = self._document_check_access('recruitment.request', request_id).sudo()
        except (AccessError, MissingError):
            return request.redirect('/my')

        allowed_states = ['draft', 'submitted', 'under_review', 'quotation_sent']
        if request.env.user.partner_id.user_type != 'employer' or recruitment_request.state not in allowed_states:
            return request.redirect('/my/recruitment')

        # Update common fields
        values = {
            'work_location': post.get('work_location'),
            'remote_work': bool(post.get('remote_work')),
            'benefits': post.get('benefits'),
            'expected_start_date': post.get('expected_start_date') or False,
        }

        # Process line_ids (job positions)
        line_commands = []

        # Handle deletions first
        delete_line_ids = post.getlist('delete_line_ids[]')
        for line_id in delete_line_ids:
            if line_id:
                line_commands.append((2, int(line_id), 0))  # Delete line

        # Process all line_ids from form
        # Group by index to get all fields for each line
        line_data_by_index = {}
        for key, value in post.items():
            if key.startswith('line_ids[') and key.endswith(']'):
                # Extract index and field name
                # Format: line_ids[0][job_title]
                parts = key.replace('line_ids[', '').replace(']', '').split('][')
                if len(parts) == 2:
                    index = int(parts[0])
                    field_name = parts[1]

                    if index not in line_data_by_index:
                        line_data_by_index[index] = {}

                    line_data_by_index[index][field_name] = value

        # Process each line
        for index in sorted(line_data_by_index.keys()):
            line_vals = line_data_by_index[index]

            # Skip if no job_title (required field)
            if not line_vals.get('job_title'):
                continue

            # Build line data
            line_data = {
                'job_title': line_vals.get('job_title'),
                'no_of_positions': int(line_vals.get('no_of_positions', 1)),
                'experience_years': int(line_vals.get('experience_years', 0)) if line_vals.get('experience_years') else 0,
                'job_description': line_vals.get('job_description', ''),
                'requirements': line_vals.get('requirements', ''),
            }

            # Add salary fields if provided
            if line_vals.get('salary_from'):
                line_data['salary_from'] = float(line_vals.get('salary_from'))
            if line_vals.get('salary_to'):
                line_data['salary_to'] = float(line_vals.get('salary_to'))

            line_id = int(line_vals.get('id', 0))

            if line_id > 0:
                # Update existing line (only if not marked for deletion)
                if str(line_id) not in delete_line_ids:
                    line_commands.append((1, line_id, line_data))
            else:
                # Create new line
                line_commands.append((0, 0, line_data))

        if line_commands:
            values['line_ids'] = line_commands

        recruitment_request.sudo().write(values)

        if post.get('button_submit'):
            recruitment_request.sudo().action_submit()

        return request.redirect(f'/my/recruitment/{recruitment_request.id}')

    @route(['/my/recruitment/<int:request_id>/applicants'], type='http', auth="user", website=True)
    def portal_my_recruitment_applicants(self, request_id, **kw):
        """View all applicants for a recruitment request in portal"""
        try:
            recruitment_request_sudo = self._document_check_access('recruitment.request', request_id).sudo()
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Get all jobs from lines
        job_ids = recruitment_request_sudo.line_ids.mapped('job_id').ids

        # Get only stages that are visible to clients
        visible_stages = request.env['hr.recruitment.stage'].sudo().search([
            ('visible_to_client', '=', True)
        ])
        visible_stage_ids = visible_stages.ids

        # Get all applicants for jobs created from this request, filtered by visible stages
        applicants = request.env['hr.applicant'].sudo().search([
            ('job_id', 'in', job_ids),
            ('stage_id', 'in', visible_stage_ids)
        ], order='create_date desc')

        # Only show visible stages
        stages = visible_stages.sorted(key=lambda s: s.sequence)

        # Calculate urgency metrics
        urgent_applicants = applicants.filtered(lambda a: a.urgency_status in ['urgent', 'overdue'])
        attention_applicants = applicants.filtered(lambda a: a.urgency_status == 'attention')

        values = {
            'page_name': 'recruitment_applicants',
            'recruitment_request': recruitment_request_sudo,
            'applicants': applicants,
            'stages': stages,
            'applicant_count': len(applicants),
            'urgent_count': len(urgent_applicants),
            'attention_count': len(attention_applicants),
        }

        return request.render("recruitment_management.portal_my_recruitment_applicants", values)

    @route(['/interview/<int:applicant_id>/<string:access_token>'], type='http', auth="public", website=True)
    def portal_interview_details(self, applicant_id, access_token, show_notes=False, **kw):
        """Public route to view interview details with access token"""
        try:
            # Find applicant with matching token
            applicant = request.env['hr.applicant'].sudo().search([
                ('id', '=', applicant_id),
                ('interview_access_token', '=', access_token),
                ('interview_share_enabled', '=', True)
            ], limit=1)

            if not applicant:
                return request.render("recruitment_management.portal_interview_access_denied")

            values = {
                'applicant': applicant,
                'show_notes': show_notes,  # Optional: control if notes are shown
                'page_name': 'interview_details',
            }

            return request.render("recruitment_management.portal_interview_details", values)

        except Exception as e:
            return request.render("recruitment_management.portal_interview_access_denied")

    @route(['/my/applicant/<int:applicant_id>/interview'], type='http', auth="user", website=True)
    def portal_my_applicant_interview(self, applicant_id, **kw):
        """Portal route for authenticated users to view interview details of their applicants"""
        try:
            # Check if user has access to this applicant through their recruitment requests
            partner = request.env.user.partner_id
            recruitment_requests = request.env['recruitment.request'].sudo().search([
                ('partner_id', '=', partner.commercial_partner_id.id)
            ])

            job_ids = recruitment_requests.mapped('line_ids.job_id').ids
            applicant = request.env['hr.applicant'].sudo().search([
                ('id', '=', applicant_id),
                ('job_id', 'in', job_ids)
            ], limit=1)

            if not applicant:
                return request.redirect('/my')

            # Check if applicant has interview details shared
            if not applicant.interview_share_enabled:
                return request.render("recruitment_management.portal_interview_access_denied")

            values = {
                'applicant': applicant,
                'show_notes': True,  # Authenticated users can see notes
                'page_name': 'interview_details',
            }

            return request.render("recruitment_management.portal_interview_details", values)

        except (AccessError, MissingError):
            return request.redirect('/my')

    @route(["/my/recruitment/get_skills"], type="jsonrpc", auth="user", website=True)
    def get_skills_by_type(self, skill_type_id=None, **kw):
        """Get skills filtered by skill type for AJAX requests"""
        if skill_type_id:
            skills = request.env["hr.skill"].sudo().search([
                ("skill_type_id", "=", int(skill_type_id)),
                ("skill_type_id.active", "=", True)
            ])
            return [{"id": skill.id, "name": skill.name} for skill in skills]
        return []

    @route(['/my/recruitment/applicant/<int:applicant_id>/download_resume'], type='http', auth='user', website=True)
    def download_applicant_resume(self, applicant_id, **kw):
        """Download applicant's resume/CV"""
        import base64
        from werkzeug.urls import url_quote

        try:
            # Get the applicant with sudo to check access
            applicant = request.env['hr.applicant'].sudo().browse(applicant_id)

            if not applicant.exists():
                return request.not_found()

            # Check if user has access to this applicant's recruitment request
            recruitment_request = applicant.recruitment_request_id
            partner = request.env.user.partner_id

            # Only allow if the user is the owner of the recruitment request
            if recruitment_request.partner_id.commercial_partner_id != partner.commercial_partner_id:
                return request.not_found()

            if not applicant.resume_attachment:
                return request.not_found()

            # Prepare file download
            filename = applicant.resume_filename or f'{applicant.partner_name}_CV.pdf'

            # Encode filename to handle non-ASCII characters
            # Use ASCII-safe name with URL encoding for Content-Disposition
            filename_ascii = filename.encode('ascii', 'ignore').decode('ascii')
            if not filename_ascii:
                filename_ascii = 'resume.pdf'

            # Decode base64 binary data
            file_content = base64.b64decode(applicant.resume_attachment)

            # Return the file with proper encoding
            return request.make_response(
                file_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', f'attachment; filename="{filename_ascii}"; filename*=UTF-8\'\'{url_quote(filename)}'),
                    ('Content-Length', len(file_content)),
                ]
            )
        except (AccessError, MissingError):
            return request.not_found()

    @route(['/my/recruitment/applicant/<int:applicant_id>/download_interview_result'], type='http', auth='user', website=True)
    def download_applicant_interview_result(self, applicant_id, **kw):
        """Download applicant's interview result/assessment"""
        import base64
        from werkzeug.urls import url_quote

        try:
            # Get the applicant with sudo to check access
            applicant = request.env['hr.applicant'].sudo().browse(applicant_id)

            if not applicant.exists():
                return request.not_found()

            # Check if user has access to this applicant's recruitment request
            recruitment_request = applicant.recruitment_request_id
            partner = request.env.user.partner_id

            # Only allow if the user is the owner of the recruitment request
            if recruitment_request.partner_id.commercial_partner_id != partner.commercial_partner_id:
                return request.not_found()

            if not applicant.interview_result_attachment:
                return request.not_found()

            # Prepare file download
            filename = applicant.interview_result_filename or f'{applicant.partner_name}_Interview_Result.pdf'

            # Encode filename to handle non-ASCII characters
            filename_ascii = filename.encode('ascii', 'ignore').decode('ascii')
            if not filename_ascii:
                filename_ascii = 'interview_result.pdf'

            # Decode base64 binary data
            file_content = base64.b64decode(applicant.interview_result_attachment)

            # Return the file with proper encoding
            return request.make_response(
                file_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', f'attachment; filename="{filename_ascii}"; filename*=UTF-8\'\'{url_quote(filename)}'),
                    ('Content-Length', len(file_content)),
                ]
            )
        except (AccessError, MissingError):
            return request.not_found()
