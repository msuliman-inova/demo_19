from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ConvertToRecruitmentWizard(models.TransientModel):
    _name = 'convert.to.recruitment.wizard'
    _description = 'Convert Opportunity to Recruitment Request'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity/Lead',
        required=True,
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Employer Company',
        required=True,
        domain="[('is_company', '=', True)]"
    )

    contact_person_id = fields.Many2one(
        'res.partner',
        string='Contact Person',
        domain="[('parent_id', '=', partner_id)]"
    )

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

    benefits = fields.Text(
        string='Benefits & Perks'
    )

    notes = fields.Text(
        string='Internal Notes',
        help='Additional notes and details from the opportunity'
    )

    # Job Line fields
    job_lines = fields.One2many(
        'convert.to.recruitment.job.line',
        'wizard_id',
        string='Job Positions',
        required=True
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-fill wizard with data from opportunity/lead"""
        res = super().default_get(fields_list)

        lead_id = self.env.context.get('active_id')
        if lead_id:
            lead = self.env['crm.lead'].browse(lead_id)

            # Set partner (company)
            if lead.partner_id:
                if lead.partner_id.is_company:
                    res['partner_id'] = lead.partner_id.id
                elif lead.partner_id.parent_id:
                    res['partner_id'] = lead.partner_id.parent_id.id
                    res['contact_person_id'] = lead.partner_id.id
                else:
                    res['partner_id'] = lead.partner_id.id

            # Extract work location from lead
            if lead.city and lead.country_id:
                res['work_location'] = f"{lead.city}, {lead.country_id.name}"
            elif lead.city:
                res['work_location'] = lead.city
            elif lead.country_id:
                res['work_location'] = lead.country_id.name

            # Pre-fill notes from CRM description
            if lead.description:
                res['notes'] = lead.description

            # Try to extract job info from description
            res['job_lines'] = [(0, 0, {
                'job_title': lead.name or 'Position',
                'no_of_positions': 1,
                'job_description': lead.description or '',
            })]

            res['lead_id'] = lead_id

        return res

    def action_convert(self):
        """Convert the opportunity to recruitment request"""
        self.ensure_one()

        if not self.job_lines:
            raise UserError(_('Please add at least one job position.'))

        # Prepare recruitment request values
        request_vals = {
            'partner_id': self.partner_id.id,
            'contact_person_id': self.contact_person_id.id if self.contact_person_id else False,
            'work_location': self.work_location,
            'remote_work': self.remote_work,
            'expected_start_date': self.expected_start_date,
            'benefits': self.benefits,
            'internal_notes': self.notes,
            'lead_id': self.lead_id.id if self.lead_id else False,
            'is_portal_request': False,
            'state': 'draft',
        }

        # Create the recruitment request
        recruitment_request = self.env['recruitment.request'].create(request_vals)

        # Create job lines
        for job_line in self.job_lines:
            line_vals = {
                'request_id': recruitment_request.id,
                'job_title': job_line.job_title,
                'no_of_positions': job_line.no_of_positions,
                'department_id': job_line.department_id.id if job_line.department_id else False,
                'emp_contract_type': job_line.emp_contract_type.id if job_line.emp_contract_type else False,
                'job_description': job_line.job_description,
                'requirements': job_line.requirements,
                'expected_degree': job_line.expected_degree.id if job_line.expected_degree else False,
                'experience_years': job_line.experience_years,
                'salary_from': job_line.salary_from,
                'salary_to': job_line.salary_to,
            }

            job_line_record = self.env['recruitment.request.line'].create(line_vals)

            # Add skills if any
            if job_line.job_skill_ids:
                job_line_record.job_skill_ids = [(6, 0, job_line.job_skill_ids.ids)]

        # Link the recruitment request to the lead
        self.lead_id.write({
            'recruitment_request_id': recruitment_request.id,
        })

        # Add a note to the lead
        self.lead_id.message_post(
            body=_('Converted to Recruitment Request: %s') % recruitment_request.name,
            subject=_('Converted to Recruitment Request')
        )

        # Return action to open the created recruitment request
        return {
            'name': _('Recruitment Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'recruitment.request',
            'view_mode': 'form',
            'res_id': recruitment_request.id,
            'target': 'current',
        }


class ConvertToRecruitmentJobLine(models.TransientModel):
    _name = 'convert.to.recruitment.job.line'
    _description = 'Job Line for Conversion Wizard'

    wizard_id = fields.Many2one(
        'convert.to.recruitment.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    job_title = fields.Char(
        string='Job Title',
        required=True
    )

    no_of_positions = fields.Integer(
        string='Number of Positions',
        required=True,
        default=1
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department'
    )

    emp_contract_type = fields.Many2one(
        'hr.contract.type',
        string='Contract Type'
    )

    job_description = fields.Text(
        string='Job Description'
    )

    requirements = fields.Text(
        string='Requirements & Qualifications'
    )

    expected_degree = fields.Many2one(
        'hr.recruitment.degree',
        string='Minimum Education Level'
    )

    experience_years = fields.Integer(
        string='Required Experience (Years)',
        default=0
    )

    job_skill_ids = fields.Many2many(
        'hr.skill',
        string='Required Skills'
    )

    salary_from = fields.Monetary(
        string='Minimum Salary',
        currency_field='currency_id'
    )

    salary_to = fields.Monetary(
        string='Maximum Salary',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
