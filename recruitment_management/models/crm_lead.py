from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    recruitment_request_id = fields.Many2one(
        'recruitment.request',
        string='Recruitment Request',
        readonly=True
    )

    is_recruitment_lead = fields.Boolean(
        string='Is Recruitment Lead',
        compute='_compute_is_recruitment_lead',
        store=True
    )

    subject_id = fields.Many2one(
        'contact.subject',
        string='Subject',
        tracking=True
    )

    # Contact preferences
    preferred_contact_method = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('whatsapp', 'WhatsApp')
    ], string='Preferred Contact Method', tracking=True)

    best_time_to_contact = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening')
    ], string='Best Time to Contact', tracking=True)

    country_id = fields.Many2one(
        'res.country',
        string='Country/Location',
        tracking=True
    )

    # For employers/clients
    position_to_fill = fields.Char(
        string='Position/Role to Fill',
        tracking=True
    )

    category = fields.Selection([
        ('grey', 'Grey Collar'),
        ('blue', 'Blue Collar'),
        ('white', 'White Collar'),
        ('emiratization', 'Emiratization'),
        ('others', 'Others')
    ], string='Category', tracking=True, help='Category type for recruitment')

    requirement_line_ids = fields.One2many(
        'crm.lead.requirement.line',
        'lead_id',
        string='Requirements',
    )

    stage_is_new = fields.Boolean(
        related='stage_id.is_new',
        string='Stage Is New',
    )

    email_attach = fields.Binary(
        string='Email Attachment',
        attachment=True,
    )
    email_attach_filename = fields.Char(string='Email Attachment Filename')

    service_agreement = fields.Binary(
        string='Service Agreement',
        attachment=True,
    )
    service_agreement_filename = fields.Char(string='Service Agreement Filename')

    demand_letter = fields.Binary(
        string='Demand Letter',
        attachment=True,
    )
    demand_letter_filename = fields.Char(string='Demand Letter Filename')

    def action_preview_email_attach(self):
        self.ensure_one()
        return self._action_preview_attachment('email_attach')

    def action_preview_service_agreement(self):
        self.ensure_one()
        return self._action_preview_attachment('service_agreement')

    def action_preview_demand_letter(self):
        self.ensure_one()
        return self._action_preview_attachment('demand_letter')

    def _action_preview_attachment(self, field_name):
        """Open attachment file in a new browser tab for preview"""
        if not self[field_name]:
            raise UserError(_('No file uploaded to preview.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=crm.lead&field=%s&id=%d&download=false' % (field_name, self.id),
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            # If subject_id is provided, set the name field to the subject name
            if vals.get('subject_id'):
                subject = self.env['contact.subject'].browse(vals['subject_id'])
                if subject.exists():
                    vals['name'] = subject.name

        return super(CrmLead, self).create(vals_list)

    @api.depends('recruitment_request_id')
    def _compute_is_recruitment_lead(self):
        for lead in self:
            lead.is_recruitment_lead = bool(lead.recruitment_request_id)

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

    # Stage flag ordering for determining forward/backward movement
    STAGE_FLAG_ORDER = {
        'is_new': 1,
        'is_in_progress': 2,
        'is_confirmed': 3,
        'is_completed': 4,
        'is_lost': 5,
    }

    def _get_stage_flag(self, stage):
        """Get the active flag name for a stage"""
        for flag in self.STAGE_FLAG_ORDER:
            if stage[flag]:
                return flag
        return False

    def _get_stage_order(self, stage):
        """Get numeric order for a stage based on its flag"""
        flag = self._get_stage_flag(stage)
        return self.STAGE_FLAG_ORDER.get(flag, 0)

    def write(self, vals):
        # Stage transition validation (only forward)
        if 'stage_id' in vals:
            new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            new_flag = self._get_stage_flag(new_stage)
            new_order = self._get_stage_order(new_stage)

            for lead in self:
                if lead.type != 'opportunity':
                    continue

                old_order = self._get_stage_order(lead.stage_id)

                # Only validate forward movement
                if new_order <= old_order:
                    continue

                old_flag = self._get_stage_flag(lead.stage_id)

                # New → In Progress: block only if no employee assigned
                if old_flag == 'is_new' and new_flag == 'is_in_progress':
                    if not lead.assigned_employee_id:
                        raise UserError(_(
                            'Please assign an employee before moving to "In Progress".'
                        ))

                # In Progress → Confirmed: require service agreement
                if old_flag == 'is_in_progress' and new_flag == 'is_confirmed':
                    if not lead.service_agreement:
                        raise UserError(
                            _('Service Agreement is required before moving to "Confirmed".')
                        )

                # Confirmed → Completed: require demand letter
                if old_flag == 'is_confirmed' and new_flag == 'is_completed':
                    if not lead.demand_letter:
                        raise UserError(
                            _('Demand Letter is required before moving to "Completed".')
                        )

        res = super(CrmLead, self).write(vals)

        # Check if stage_id changed for recruitment request sync
        if 'stage_id' in vals:
            for lead in self:
                new_stage = lead.stage_id.name.lower()
                if lead.recruitment_request_id and new_stage == 'qualified':
                    lead.recruitment_request_id.state = 'under_review'
        return res

    def action_new_quotation(self):
        """Override default create quotation to include recruitment request lines"""
        self.ensure_one()

        # If this is a recruitment lead, use custom quotation creation
        if self.recruitment_request_id:
            return self.recruitment_request_id.action_send_quotation()

        # Otherwise, use standard CRM quotation creation
        return super(CrmLead, self).action_new_quotation()

    def action_convert_to_recruitment(self):
        """Directly convert opportunity to recruitment request using Inquiry Details"""
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_('Please set a customer before converting to recruitment.'))

        # Determine partner (company)
        if self.partner_id.is_company:
            partner_id = self.partner_id.id
            contact_person_id = False
        elif self.partner_id.parent_id:
            partner_id = self.partner_id.parent_id.id
            contact_person_id = self.partner_id.id
        else:
            partner_id = self.partner_id.id
            contact_person_id = False

        # Build work location
        work_location = ''
        if self.city and self.country_id:
            work_location = '%s, %s' % (self.city, self.country_id.name)
        elif self.city:
            work_location = self.city
        elif self.country_id:
            work_location = self.country_id.name
        else:
            work_location = 'TBD'

        # Create recruitment request
        request_vals = {
            'partner_id': partner_id,
            'contact_person_id': contact_person_id,
            'work_location': work_location,
            'internal_notes': self.description or '',
            'lead_id': self.id,
            'is_portal_request': False,
            'state': 'draft',
        }
        recruitment_request = self.env['recruitment.request'].create(request_vals)

        # Get default contract type
        default_contract_type = self.env['hr.contract.type'].search([], limit=1)
        if not default_contract_type:
            raise UserError(_('No contract types found. Please create at least one contract type first.'))

        # Create job lines from inquiry details (requirement_line_ids)
        if self.requirement_line_ids:
            for line in self.requirement_line_ids:
                self.env['recruitment.request.line'].create({
                    'request_id': recruitment_request.id,
                    'job_title': line.description or line.product_id.name,
                    'no_of_positions': int(line.quantity) or 1,
                    'job_description': line.description or '',
                    'emp_contract_type': default_contract_type.id,
                })
        else:
            # Fallback: create a single line from opportunity name
            self.env['recruitment.request.line'].create({
                'request_id': recruitment_request.id,
                'job_title': self.name or 'Position',
                'no_of_positions': 1,
                'job_description': self.description or '',
                'emp_contract_type': default_contract_type.id,
            })

        # Link recruitment request to the lead
        self.write({'recruitment_request_id': recruitment_request.id})

        # Log message
        self.message_post(
            body=_('Converted to Recruitment Request: %s') % recruitment_request.name,
            subject=_('Converted to Recruitment Request'),
        )

        return {
            'name': _('Recruitment Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'recruitment.request',
            'view_mode': 'form',
            'res_id': recruitment_request.id,
            'target': 'current',
        }

    def _prepare_opportunity_quotation_context(self):
        """Add requirement lines as default order lines on the quotation"""
        context = super()._prepare_opportunity_quotation_context()
        if self.requirement_line_ids:
            order_lines = []
            for line in self.requirement_line_ids:
                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.description or line.product_id.name,
                    'product_uom_qty': line.quantity,
                    'price_unit': line.price_unit,
                }))
            context['default_order_line'] = order_lines
        return context
