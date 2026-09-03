from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class RecruitmentRequest(models.Model):
    _name = 'recruitment.request'
    _description = 'Recruitment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    # Basic Information
    name = fields.Char(
        string='Request Number',
        required=True,
        copy=False,
        readonly=True,
        tracking=True,
        default=lambda self: _('New')
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Employer Company',
        required=True,
        tracking=True,
    )

    contact_person_id = fields.Many2one(
        'res.partner',
        string='Contact Person',
        tracking=True,
    )

    user_id = fields.Many2one(
        'res.users',
        string='Recruitment Officer',
        default=lambda self: self.env.user,
        tracking=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    is_portal_request = fields.Boolean(
        string='Portal Request',
        default=False,
        readonly=True,
        help='Indicates if this request was created from the customer portal'
    )

    lead_id = fields.Many2one(
        'crm.lead',
        string='Source Opportunity/Lead',
        readonly=True,
        tracking=True,
        help='The CRM opportunity/lead that was converted to this recruitment request'
    )

    # Job Lines (Multiple Jobs in One Request)
    line_ids = fields.One2many(
        'recruitment.request.line',
        'request_id',
        string='Job Lines',
        copy=True,
        required=False
    )

    no_of_positions = fields.Integer(
        string='Number of Positions',
        compute='_compute_totals',
        store=True,
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    benefits = fields.Text(
        string='Benefits & Perks'
    )

    # Location & Schedule
    work_location = fields.Char(
        string='Work Location',
        required=True
    )

    remote_work = fields.Boolean(
        string='Remote Work Available'
    )

    expected_start_date = fields.Date(
        string='Expected Start Date'
    )

    # Pricing & Financial - Commented out as per requirement
    # service_fee = fields.Monetary(
    #     string='Service Fee',
    #     currency_field='currency_id',
    #     compute='_compute_totals',
    #     store=True,
    #     readonly=False
    # )

    # additional_services = fields.Many2many(
    #     'recruitment.additional.service',
    #     string='Additional Services'
    # )

    # additional_fee = fields.Monetary(
    #     string='Additional Services Fee',
    #     currency_field='currency_id',
    #     compute='_compute_additional_fee',
    #     store=True
    # )

    # total_amount = fields.Monetary(
    #     string='Total Amount',
    #     currency_field='currency_id',
    #     compute='_compute_total_amount',
    #     store=True
    # )

    # discount_percentage = fields.Float(
    #     string='Discount (%)',
    #     default=0.0
    # )

    # discount_amount = fields.Monetary(
    #     string='Discount Amount',
    #     currency_field='currency_id',
    #     compute='_compute_total_amount',
    #     store=True
    # )

    # final_amount = fields.Monetary(
    #     string='Final Amount',
    #     currency_field='currency_id',
    #     compute='_compute_total_amount',
    #     store=True
    # )

    # Invoicing Policy
    invoicing_policy = fields.Selection([
        ('all', 'Invoice Full Amount'),
        ('hired', 'Invoice Based on Hired Applicants'),
    ], string='Invoicing Policy', default='hired', required=True,
        help='All: Invoice full amount upfront\nHired: Invoice per hired applicant')

    hired_count = fields.Integer(
        string='Hired Applicants',
        compute='_compute_hired_count',
        store=False
    )

    invoiced_count = fields.Integer(
        string='Invoiced Hired Count',
        compute='_compute_invoiced_count',
        store=False,
        help='Number of hired applicants already invoiced'
    )

    uninvoiced_hired_count = fields.Integer(
        string='Uninvoiced Hired Count',
        compute='_compute_uninvoiced_hired_count',
        store=False,
        help='Number of hired applicants not yet invoiced'
    )

    invoiced_hired_applicant_ids = fields.Many2many(
        'hr.applicant',
        'recruitment_request_invoiced_applicant_rel',
        'request_id',
        'applicant_id',
        string='Invoiced Hired Applicants',
        help='Track which hired applicants have already been invoiced'
    )

    # Related Records
    lead_id = fields.Many2one(
        'crm.lead',
        string='CRM Lead',
        readonly=True,
        copy=False
    )

    job_ids = fields.Many2many(
        'hr.job',
        string='Job Positions',
        compute='_compute_job_ids',
        store=False
    )

    job_count = fields.Integer(
        string='Job Count',
        compute='_compute_job_ids',
        store=False
    )

    applicant_ids = fields.Many2many(
        'hr.applicant',
        string='Applicants',
        compute='_compute_applicant_ids',
        store=False
    )

    applicant_count = fields.Integer(
        string='Applicant Count',
        compute='_compute_applicant_ids',
        store=False
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        readonly=True,
        copy=False
    )

    invoice_ids = fields.One2many(
        'account.move',
        compute='_compute_invoice_ids',
        string='Invoices'
    )

    invoice_count = fields.Integer(
        compute='_compute_invoice_ids',
        string='Invoice Count'
    )

    # Status & Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('quotation_sent', 'Quotation Sent'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent'),
    ], string='Priority', default='0')

    color = fields.Integer(string='Color Index', default=0)

    # Dates
    submission_date = fields.Datetime(
        string='Submission Date',
        readonly=True
    )

    review_date = fields.Datetime(
        string='Review Date',
        readonly=True
    )

    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True
    )

    deadline_date = fields.Date(
        string='Deadline Date'
    )

    # Notes
    internal_notes = fields.Text(
        string='Internal Notes'
    )

    rejection_reason = fields.Text(
        string='Rejection Reason'
    )

    # Portal
    def _compute_access_url(self):
        super(RecruitmentRequest, self)._compute_access_url()
        for request in self:
            request.access_url = f'/my/recruitment/{request.id}'

    def format_amount(self, amount):
        """Format amount with currency for display"""
        if amount and self.currency_id:
            return f"{amount:,.2f} {self.currency_id.symbol}"
        return f"{amount:,.2f}" if amount else "0.00"

    @api.model
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('recruitment.request') or _('New')

        records = super(RecruitmentRequest, self).create(vals_list)
        return records

    @api.depends('line_ids.no_of_positions')
    def _compute_totals(self):
        """Calculate totals from all job lines"""
        for request in self:
            request.no_of_positions = sum(request.line_ids.mapped('no_of_positions'))
            # request.service_fee = sum(request.line_ids.mapped('service_fee'))  # Commented out


    # Pricing calculation methods - Commented out as per requirement
    # @api.depends('additional_services', 'additional_services.price')
    # def _compute_additional_fee(self):
    #     for request in self:
    #         request.additional_fee = sum(request.additional_services.mapped('price'))

    # @api.depends('service_fee', 'additional_fee', 'discount_percentage', 'no_of_positions')
    # def _compute_total_amount(self):
    #     for request in self:
    #         request.total_amount = request.service_fee + request.additional_fee
    #         request.discount_amount = request.total_amount * (request.discount_percentage / 100)
    #         request.final_amount = request.total_amount - request.discount_amount

    @api.depends('line_ids.job_id')
    def _compute_job_ids(self):
        for request in self:
            request.job_ids = request.line_ids.mapped('job_id')
            request.job_count = len(request.job_ids)

    @api.depends('line_ids.job_id', 'line_ids.job_id.application_ids')
    def _compute_applicant_ids(self):
        """Get all applicants for all jobs created from this request"""
        for request in self:
            # Get all jobs from lines
            jobs = request.line_ids.mapped('job_id')
            # Get all applicants from those jobs
            applicants = jobs.mapped('application_ids')
            request.applicant_ids = applicants
            request.applicant_count = len(applicants)

    @api.depends('line_ids.job_id', 'line_ids.job_id.application_ids', 'line_ids.job_id.application_ids.stage_id')
    def _compute_hired_count(self):
        """Count hired applicants"""
        for request in self:
            jobs = request.line_ids.mapped('job_id')
            applicants = jobs.mapped('application_ids')
            # Count applicants in 'hired' stage
            hired = applicants.filtered(lambda a: a.stage_id.hired_stage if hasattr(a.stage_id, 'hired_stage') else False)
            request.hired_count = len(hired)

    @api.depends('invoiced_hired_applicant_ids')
    def _compute_invoiced_count(self):
        """Count invoiced hired applicants"""
        for request in self:
            request.invoiced_count = len(request.invoiced_hired_applicant_ids)

    @api.depends('line_ids.job_id', 'line_ids.job_id.application_ids', 'line_ids.job_id.application_ids.stage_id', 'invoiced_hired_applicant_ids')
    def _compute_uninvoiced_hired_count(self):
        """Count uninvoiced hired applicants"""
        for request in self:
            uninvoiced = request._get_uninvoiced_hired_applicants()
            request.uninvoiced_hired_count = len(uninvoiced)

    @api.depends('sale_order_id', 'sale_order_id.invoice_ids')
    def _compute_invoice_ids(self):
        for request in self:
            if request.sale_order_id:
                request.invoice_ids = request.sale_order_id.invoice_ids
                request.invoice_count = len(request.invoice_ids)
            else:
                request.invoice_ids = False
                request.invoice_count = 0

    def action_submit(self):
        """Submit recruitment request and create CRM lead"""
        for request in self:
            if not request.line_ids:
                raise ValidationError(_('At least one job line is required before submission.'))

            # Build job description from all lines
            job_descriptions = []
            for line in request.line_ids:
                job_descriptions.append(f"<p><strong>{line.job_title}</strong> ({line.no_of_positions} positions)</p>")

            # Create CRM Lead
            lead_vals = {
                'name': f'Recruitment: {request.partner_id.name} - {len(request.line_ids)} Job(s)',
                'partner_id': request.partner_id.id,
                'contact_name': request.contact_person_id.name if request.contact_person_id else False,
                'email_from': request.contact_person_id.email if request.contact_person_id else request.partner_id.email,
                'phone': request.contact_person_id.phone if request.contact_person_id else request.partner_id.phone,
                'user_id': request.user_id.id,
                'team_id': self.env.ref('recruitment_management.recruitment_sales_team',
                                        raise_if_not_found=False).id if self.env.ref(
                    'recruitment_management.recruitment_sales_team', raise_if_not_found=False) else False,
                'type': 'opportunity',
                # 'expected_revenue': request.final_amount,  # Removed as per requirement
                'description': f"""
                    <p><strong>Job Positions:</strong></p>
                    {''.join(job_descriptions)}
                    <p><strong>Total Positions:</strong> {request.no_of_positions}</p>
                    <p><strong>Location:</strong> {request.work_location}</p>
                """,
                'recruitment_request_id': request.id,
            }
            lead = self.env['crm.lead'].create(lead_vals)

            request.write({
                'state': 'submitted',
                'submission_date': fields.Datetime.now(),
                'lead_id': lead.id,
            })

            # Send notification email
            template = self.env.ref('recruitment_management.email_template_request_submitted', raise_if_not_found=False)
            if template:
                template.send_mail(request.id, force_send=True)

            # Log message
            request.message_post(
                body=_('Recruitment request submitted and CRM lead created.'),
                subject=_('Request Submitted')
            )

    def action_review(self):
        """Move to under review status"""
        self.write({
            'state': 'under_review',
            'review_date': fields.Datetime.now(),
        })

    def action_send_quotation(self):
        """Create quotation (sale order) with pre-filled data from recruitment request"""
        self.ensure_one()

        if not self.line_ids:
            raise ValidationError(_('No recruitment lines found. Please add at least one job position.'))

        # Get recruitment service product
        recruitment_product = self.env.ref('recruitment_management.product_recruitment_service', raise_if_not_found=False)
        if not recruitment_product:
            raise ValidationError(_('Recruitment service product not found. Please check module data.'))

        # Prepare sale order lines from recruitment request lines
        order_lines = []
        for line in self.line_ids:
            if line.no_of_positions > 0:
                # Build simple description with job title
                description = _('Recruitment Service: %s') % line.job_title

                # Add salary range if available
                if line.salary_from or line.salary_to:
                    salary_info = _('\nSalary Range: ')
                    if line.salary_from and line.salary_to:
                        salary_info += _('%s - %s %s') % (
                            '{:,.2f}'.format(line.salary_from),
                            '{:,.2f}'.format(line.salary_to),
                            line.currency_id.name or ''
                        )
                    elif line.salary_from:
                        salary_info += _('From %s %s') % (
                            '{:,.2f}'.format(line.salary_from),
                            line.currency_id.name or ''
                        )
                    elif line.salary_to:
                        salary_info += _('Up to %s %s') % (
                            '{:,.2f}'.format(line.salary_to),
                            line.currency_id.name or ''
                        )
                    description += salary_info

                # Add fee percentage
                if line.pricing_percentage > 0:
                    description += _('\nFee Percentage: %s%%') % line.pricing_percentage

                line_vals = {
                    'product_id': recruitment_product.id,
                    'name': description,
                    'product_uom_qty': line.no_of_positions,
                    'price_unit': 0.0,  # Price to be set manually
                    'fee_percentage': line.pricing_percentage,  # Pass fee percentage to sale line
                }
                order_lines.append((0, 0, line_vals))

        # Validate that we have lines to create
        if not order_lines:
            raise ValidationError(_('No valid lines to create quotation. Please check job positions.'))

        # Prepare context with default values for new sale order
        context = {
            'default_partner_id': self.partner_id.id,
            'default_user_id': self.user_id.id if self.user_id else self.env.user.id,
            'default_origin': self.name,
            'default_recruitment_request_id': self.id,
            'default_order_line': order_lines,
        }

        # Add CRM lead/opportunity if exists
        if self.lead_id:
            context['default_opportunity_id'] = self.lead_id.id

        # Return action to open sale order form with pre-filled data
        return {
            'name': _('Create Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': context,
        }

    def action_approve(self):
        """Approve request and create sale order"""
        for request in self:
            # Validation removed as per requirement - no more pricing fields
            # if not request.final_amount:
            #     raise ValidationError(_('Please set service fee before approval.'))

            # # Create Sale Order
            # sale_order_vals = {
            #     'partner_id': request.partner_id.id,
            #     'user_id': request.user_id.id,
            #     'origin': request.name,
            #     'recruitment_request_id': request.id,
            #     'order_line': [
            #         (0, 0, {
            #             'name': f'Recruitment Service: {request.job_title}',
            #             'product_id': self.env.ref('recruitment_management.product_recruitment_service').id,
            #             'product_uom_qty': request.no_of_positions,
            #             'price_unit': request.service_fee / request.no_of_positions if request.no_of_positions else 0,
            #         })
            #     ]
            # }
            #
            # # Add additional services
            # for service in request.additional_services:
            #     sale_order_vals['order_line'].append(
            #         (0, 0, {
            #             'name': service.name,
            #             'product_id': service.product_id.id,
            #             'product_uom_qty': 1,
            #             'price_unit': service.price,
            #         })
            #     )
            #
            # sale_order = self.env['sale.order'].create(sale_order_vals)

            request.write({
                'state': 'approved',
                'approval_date': fields.Datetime.now(),
                # 'sale_order_id': sale_order.id,
            })

            # Send approval email
            template = self.env.ref('recruitment_management.email_template_request_approved', raise_if_not_found=False)
            if template:
                template.send_mail(request.id, force_send=True)

    def action_convert_to_job(self):
        """Convert approved request lines to job positions"""
        self.ensure_one()

        if self.state not in ['approved', 'in_progress']:
            raise UserError(_('Only approved requests can be converted to job positions.'))

        if not self.line_ids:
            raise UserError(_('No job lines found to convert.'))

        # Check if any lines are already converted
        already_converted = self.line_ids.filtered(lambda l: l.job_id)
        if already_converted:
            raise UserError(_('Some job lines have already been converted to job positions. Line(s): %s') % ', '.join(already_converted.mapped('job_title')))

        # Add work location if available
        location_partner = False
        if self.work_location:
            location_partner = self.env['res.partner'].search([
                ('name', 'ilike', self.work_location),
                '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)
            ], limit=1)

        # Create job positions for each line
        created_jobs = self.env['hr.job']
        # Determine job type: portal requests are always external
        job_type = 'external' if self.is_portal_request else 'internal'

        for line in self.line_ids:
            # Prepare job values
            job_vals = {
                'name': line.job_title,
                'partner_id': self.partner_id.id,
                'department_id': line.department_id.id if line.department_id else False,
                'no_of_recruitment': line.no_of_positions,
                'company_id': self.company_id.id,
                'description': line.job_description or '',
                'requirements': line.requirements or '',
                'contract_type_id': line.emp_contract_type.id if line.emp_contract_type else False,
                'user_id': self.user_id.id if self.user_id else False,
                'address_id': location_partner.id if location_partner else False,
                'job_type': job_type,  # External for portal requests, internal for backend
                'salary_min': line.salary_from if line.salary_from else 0.0,
                'salary_max': line.salary_to if line.salary_to else 0.0,
            }

            # Add expected degree if available
            if line.expected_degree:
                job_vals['expected_degree'] = line.expected_degree.id

            # Add skills if available - convert to job_skill_ids format
            if line.job_skill_ids:
                job_skill_commands = []
                for skill in line.job_skill_ids:
                    # Get default skill level (first available level for this skill type)
                    default_level = False
                    if skill.skill_type_id:
                        default_level = self.env['hr.skill.level'].search([
                            ('skill_type_id', '=', skill.skill_type_id.id)
                        ], limit=1, order='level_progress asc')

                    # Only add skill if we have a valid skill level
                    if default_level:
                        job_skill_commands.append((0, 0, {
                            'skill_id': skill.id,
                            'skill_level_id': default_level.id,
                            'skill_type_id': skill.skill_type_id.id if skill.skill_type_id else False,
                        }))

                if job_skill_commands:
                    job_vals['job_skill_ids'] = job_skill_commands

            # Create the job position
            job = self.env['hr.job'].create(job_vals)

            # Link job to line
            line.job_id = job.id
            created_jobs |= job

            # Log message on the line
            line.request_id.message_post(
                body=_('Job position "%s" created from line.') % line.job_title,
                subject=_('Job Position Created')
            )

        # Update state
        if self.state == 'approved':
            self.write({'state': 'in_progress'})

        # Return action to view created jobs
        return {
            'name': _('Created Job Positions'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.job',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_jobs.ids)],
            'context': {
                'default_job_type': job_type,
                'default_partner_id': self.partner_id.id,
            },
        }

    def action_complete(self):
        """Mark recruitment request as completed and unpublish related job positions"""
        for request in self:
            if not request.invoice_ids:
                raise UserError(_('Cannot complete request without any invoices.'))

            # Unpublish all related job positions
            jobs = request.line_ids.mapped('job_id')
            if jobs:
                jobs.write({'website_published': False})

            request.write({'state': 'completed'})

    def action_cancel(self):
        """Cancel recruitment request"""
        for request in self:
            if request.state in ['completed']:
                raise UserError(_('Cannot cancel a completed request.'))
            request.state = 'cancelled'

    def action_view_lead(self):
        """View related CRM lead"""
        self.ensure_one()
        return {
            'name': _('CRM Lead'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.lead_id.id,
        }

    def action_view_job(self):
        """View related job positions"""
        self.ensure_one()
        job_ids = self.line_ids.mapped('job_id').ids

        if not job_ids:
            raise UserError(_('No job positions have been created yet.'))

        return {
            'name': _('Job Positions'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.job',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', job_ids)],
        }

    def action_view_applicants(self):
        """View all applicants for jobs created from this request"""
        self.ensure_one()

        # Get applicant IDs directly from jobs
        applicant_ids = self.line_ids.mapped('job_id').mapped('application_ids').ids

        if not applicant_ids:
            raise UserError(_('No applicants found for this recruitment request yet.'))

        return {
            'name': _('Applicants for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.applicant',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', applicant_ids)],
            'context': {
                'default_job_id': self.line_ids.mapped('job_id')[0].id if self.line_ids.mapped('job_id') else False,
            }
        }

    def action_view_sale_order(self):
        """View related sale order"""
        self.ensure_one()
        return {
            'name': _('Sales Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
        }

    def action_view_invoices(self):
        """View related invoices"""
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
        }

    def _get_uninvoiced_hired_applicants(self):
        """Get hired applicants that have not been invoiced yet"""
        self.ensure_one()

        # Get all hired applicants
        jobs = self.line_ids.mapped('job_id')
        applicants = jobs.mapped('application_ids')
        hired_applicants = applicants.filtered(
            lambda a: a.stage_id.hired_stage if hasattr(a.stage_id, 'hired_stage') else False
        )

        # Filter out already invoiced applicants
        uninvoiced_hired = hired_applicants - self.invoiced_hired_applicant_ids

        return uninvoiced_hired

    def action_update_delivered_qty(self):
        """Update delivered quantity on related SO lines based on hired applicants"""
        self.ensure_one()

        if not self.sale_order_id:
            raise UserError(_('No sale order linked to this recruitment request.'))

        if self.sale_order_id.state not in ['sale', 'done']:
            raise UserError(_('Sale order must be confirmed before updating delivered quantities.'))

        # Ensure recruitment product uses delivery-based invoicing
        recruitment_product = self.env.ref('recruitment_management.product_recruitment_service', raise_if_not_found=False)
        if recruitment_product and recruitment_product.invoice_policy != 'delivery':
            recruitment_product.sudo().write({
                'invoice_policy': 'delivery',
                'service_type': 'manual',
            })

        so_lines = self.sale_order_id.order_line.filtered(
            lambda l: l.product_id == recruitment_product
        )

        if not so_lines:
            raise UserError(_('No recruitment service lines found in the sale order.'))

        # Ensure all SO lines use manual delivery method
        for sol in so_lines:
            if sol.qty_delivered_method != 'manual':
                sol.sudo().write({'qty_delivered_method': 'manual'})

        # Count hired applicants per recruitment request line
        for req_line in self.line_ids:
            if not req_line.job_id:
                continue

            hired = req_line.job_id.application_ids.filtered(
                lambda a: a.stage_id.hired_stage if hasattr(a.stage_id, 'hired_stage') else False
            )
            hired_count = len(hired)

            # Find matching SO line by job title in description
            so_line = so_lines[0]  # Default to first
            for sol in so_lines:
                if req_line.job_title in (sol.name or ''):
                    so_line = sol
                    break

            # Update delivered quantity
            so_line.write({'qty_delivered': hired_count})

        # Post message
        total_delivered = sum(so_lines.mapped('qty_delivered'))
        total_ordered = sum(so_lines.mapped('product_uom_qty'))
        self.message_post(
            body=_('Delivered quantities updated: %s/%s positions filled.') % (
                int(total_delivered), int(total_ordered)),
            subject=_('Delivered Quantities Updated'),
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class RecruitmentPricing(models.Model):
    _name = 'recruitment.pricing'
    _description = 'Recruitment Service Pricing'
    _order = 'emp_contract_type, min_salary'

    name = fields.Char(string='Pricing Rule Name', required=True)
    emp_contract_type = fields.Many2one('hr.contract.type' , string='Contract Type', required=True,)

    min_experience = fields.Integer(string='Min Experience (Years)', default=0)
    max_experience = fields.Integer(string='Max Experience (Years)', default=99)

    min_salary = fields.Monetary(string='Min Salary Range', currency_field='currency_id', default=0.0)
    max_salary = fields.Monetary(string='Max Salary Range', currency_field='currency_id', default=0.0)

    percentage = fields.Float(string='Fee Percentage (%)', required=True, help='Percentage to calculate service fee based on salary')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(default=True)

    _percentage_not_null = models.Constraint(
        'CHECK(percentage IS NOT NULL)',
        'Percentage cannot be null!',
    )
    _percentage_positive = models.Constraint(
        'CHECK(percentage >= 0)',
        'Percentage must be positive!',
    )

    def init(self):
        """Update existing records with NULL percentage to 0.0"""
        self.env.cr.execute("""
            UPDATE recruitment_pricing
            SET percentage = 0.0
            WHERE percentage IS NULL
        """)


class RecruitmentAdditionalService(models.Model):
    _name = 'recruitment.additional.service'
    _description = 'Additional Recruitment Services'

    name = fields.Char(string='Service Name', required=True)
    description = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    price = fields.Monetary(string='Price', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(default=True)