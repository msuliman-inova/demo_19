from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta
import uuid


class HrApplicant(models.Model):
    _inherit = ['hr.applicant', 'portal.mixin']
    _name = 'hr.applicant'

    time_to_fill_date = fields.Date(
        string='Time to Fill Deadline',
        help='Target date to fill this position. Used to calculate urgency and remaining time.',
        copy=False
    )

    guarantee_period_end = fields.Date(
        string='Guarantee Period End',
        help='End date of replacement guarantee. If hired employee leaves before this date, customer is eligible for free replacement.',
        copy=False
    )

    contract_salary = fields.Monetary(
        string='Contract Salary',
        help='Actual salary agreed in the contract',
        currency_field='company_currency_id',
        copy=False
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )

    post_hire_reminder_created = fields.Boolean(
        string='Post-Hire Reminder Created',
        default=False,
        copy=False,
        help='Indicates if the 15-day post-hire reminder activity has been created'
    )

    is_under_guarantee = fields.Boolean(
        string='Under Guarantee',
        compute='_compute_is_under_guarantee',
        store=True,
        help='True if today is before the guarantee period end date'
    )

    guarantee_days_remaining = fields.Integer(
        string='Guarantee Days Remaining',
        compute='_compute_is_under_guarantee',
        store=True,
        help='Number of days remaining in the guarantee period'
    )

    # Interview Recording Fields
    interview_platform = fields.Selection([
        ('zoom', 'Zoom'),
        ('teams', 'Microsoft Teams'),
        ('meet', 'Google Meet'),
        ('other', 'Other'),
    ], string='Interview Platform', copy=False)

    interview_meeting_url = fields.Char(
        string='Meeting Link',
        copy=False,
        help='Link to the video conference meeting'
    )

    interview_date = fields.Datetime(
        string='Interview Date/Time',
        copy=False
    )

    google_drive_folder_url = fields.Char(
        string='Google Drive Folder',
        copy=False,
        help='Google Drive folder URL where interview recordings are stored'
    )

    google_drive_recording_urls = fields.Text(
        string='Recording Links',
        copy=False,
        help='Google Drive links to interview recordings (one per line)'
    )

    interview_notes = fields.Html(
        string='Interview Notes',
        copy=False
    )

    # Interview Result Attachment
    interview_result_attachment = fields.Binary(
        string='Interview Result',
        copy=False,
        help='Interview result document or assessment report'
    )

    interview_result_filename = fields.Char(
        string='Interview Result Filename',
        copy=False
    )

    # Resume/Attachment Field
    resume_attachment = fields.Binary(
        string='Resume/CV',
        copy=False,
        help='Resume or CV file uploaded from platform or manually'
    )

    resume_filename = fields.Char(
        string='Resume Filename',
        copy=False
    )

    # Portal Sharing Fields
    interview_share_enabled = fields.Boolean(
        string='Share Interview with Client',
        default=False,
        copy=False,
        help='Enable portal access for client to view interview details and recordings'
    )

    interview_access_token = fields.Char(
        string='Interview Access Token',
        copy=False,
        readonly=True,
        help='Unique token for secure interview access'
    )

    interview_share_url = fields.Char(
        string='Interview Share URL',
        compute='_compute_interview_share_url',
        help='Secure URL to share interview details with client'
    )

    days_remaining = fields.Integer(
        string='Days Remaining',
        compute='_compute_days_remaining',
        store=True,
        help='Number of days remaining until the time to fill deadline'
    )

    urgency_status = fields.Selection([
        ('normal', 'Normal'),
        ('attention', 'Needs Attention'),
        ('urgent', 'Urgent'),
        ('overdue', 'Overdue'),
    ], string='Urgency Status', compute='_compute_urgency_status', store=True)

    urgency_color = fields.Char(
        string='Urgency Color',
        compute='_compute_urgency_color',
        store=True,
        help='Color code for urgency display'
    )

    @api.depends('guarantee_period_end')
    def _compute_is_under_guarantee(self):
        """Calculate if applicant is still under guarantee period"""
        today = date.today()
        for applicant in self:
            if applicant.guarantee_period_end:
                delta = applicant.guarantee_period_end - today
                applicant.guarantee_days_remaining = delta.days
                applicant.is_under_guarantee = delta.days >= 0
            else:
                applicant.guarantee_days_remaining = 0
                applicant.is_under_guarantee = False

    @api.depends('time_to_fill_date')
    def _compute_days_remaining(self):
        """Calculate days remaining until deadline"""
        today = date.today()
        for applicant in self:
            if applicant.time_to_fill_date:
                delta = applicant.time_to_fill_date - today
                applicant.days_remaining = delta.days
            else:
                applicant.days_remaining = 0

    @api.depends('time_to_fill_date', 'days_remaining', 'stage_id', 'stage_id.hired_stage')
    def _compute_urgency_status(self):
        """Compute urgency status based on remaining days and configuration"""
        # Get configuration
        config = self.env['recruitment.urgency.config'].sudo().get_config()

        for applicant in self:
            # If applicant is hired, no urgency alerts needed
            if applicant.stage_id and hasattr(applicant.stage_id, 'hired_stage') and applicant.stage_id.hired_stage:
                applicant.urgency_status = 'normal'
            elif not applicant.time_to_fill_date:
                applicant.urgency_status = 'normal'
            elif applicant.days_remaining < 0:
                applicant.urgency_status = 'overdue'
            elif applicant.days_remaining <= config.urgency_urgent_days:
                applicant.urgency_status = 'urgent'
            elif applicant.days_remaining <= config.urgency_attention_days:
                applicant.urgency_status = 'attention'
            else:
                applicant.urgency_status = 'normal'

    @api.depends('urgency_status')
    def _compute_urgency_color(self):
        """Compute urgency color based on status - using fixed colors"""
        # Fixed color map
        color_map = {
            'overdue': '#dc3545',    # Red
            'urgent': '#fd7e14',     # Orange
            'attention': '#ffc107',  # Yellow
            'normal': '#28a745',     # Green
        }

        for applicant in self:
            applicant.urgency_color = color_map.get(applicant.urgency_status, '#6c757d')

    def write(self, vals):
        """Override write to create post-hire reminder activity"""
        res = super(HrApplicant, self).write(vals)

        # Check if stage was changed
        if 'stage_id' in vals:
            for applicant in self:
                # Check if applicant is now in hired stage and reminder hasn't been created yet
                if (applicant.stage_id and
                    hasattr(applicant.stage_id, 'hired_stage') and
                    applicant.stage_id.hired_stage and
                    not applicant.post_hire_reminder_created):

                    # Create reminder activity for 15 days after hire
                    applicant._create_post_hire_reminder()
                    applicant.post_hire_reminder_created = True

        return res

    def _message_post_after_hook(self, message, msg_vals):
        """Hook to auto-populate resume_attachment from first attachment"""
        res = super()._message_post_after_hook(message, msg_vals)

        # Auto-populate resume from first attachment if not already set
        for applicant in self:
            if not applicant.resume_attachment and message.attachment_ids:
                first_attachment = message.attachment_ids[0]
                applicant.write({
                    'resume_attachment': first_attachment.datas,
                    'resume_filename': first_attachment.name,
                })

        return res

    def action_open_google_drive_folder(self):
        """Open Google Drive folder in browser"""
        self.ensure_one()
        if not self.google_drive_folder_url:
            raise UserError(_('No Google Drive folder URL configured for this applicant.'))

        return {
            'type': 'ir.actions.act_url',
            'url': self.google_drive_folder_url,
            'target': 'new',
        }

    def action_open_meeting_link(self):
        """Open video conference meeting link"""
        self.ensure_one()
        if not self.interview_meeting_url:
            raise UserError(_('No meeting link configured for this applicant.'))

        return {
            'type': 'ir.actions.act_url',
            'url': self.interview_meeting_url,
            'target': 'new',
        }

    @api.depends('interview_access_token')
    def _compute_interview_share_url(self):
        """Compute the secure share URL for interview details"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for applicant in self:
            if applicant.interview_access_token:
                applicant.interview_share_url = f"{base_url}/interview/{applicant.id}/{applicant.interview_access_token}"
            else:
                applicant.interview_share_url = False

    def action_generate_interview_token(self):
        """Generate or regenerate access token for interview sharing"""
        self.ensure_one()
        if not self.interview_access_token:
            self.interview_access_token = str(uuid.uuid4())
        self.interview_share_enabled = True
        return True

    def action_toggle_interview_sharing(self):
        """Toggle interview sharing on/off"""
        self.ensure_one()
        if self.interview_share_enabled:
            # Disable sharing
            self.interview_share_enabled = False
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Interview Sharing Disabled'),
                    'message': _('Interview details are no longer accessible via public link.'),
                    'type': 'warning',
                }
            }
        else:
            # Enable sharing and generate token if needed
            self.action_generate_interview_token()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Interview Sharing Enabled'),
                    'message': _('Interview details can now be shared via the secure link.'),
                    'type': 'success',
                }
            }

    def action_copy_interview_link(self):
        """Copy interview share link to clipboard"""
        self.ensure_one()
        if not self.interview_share_enabled:
            raise UserError(_('Please enable interview sharing first.'))

        if not self.interview_access_token:
            self.action_generate_interview_token()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Link Ready'),
                'message': _('Interview link: %s') % self.interview_share_url,
                'type': 'info',
                'sticky': True,
            }
        }

    def _get_share_url(self, redirect=False, signup_token=False, pid=False):
        """Override portal mixin to provide interview-specific URL"""
        self.ensure_one()
        if self.interview_access_token:
            return self.interview_share_url
        return super()._get_share_url(redirect=redirect, signup_token=signup_token, pid=pid)

    def get_recording_links_list(self):
        """Parse recording URLs from text field and return as list"""
        self.ensure_one()
        if not self.google_drive_recording_urls:
            return []

        # Split by newlines and filter empty lines
        links = [link.strip() for link in self.google_drive_recording_urls.split('\n') if link.strip()]
        return links

    def _create_post_hire_reminder(self):
        """Create a reminder activity 15 days after hire date"""
        self.ensure_one()

        # Calculate reminder date (15 days from today)
        reminder_date = date.today() + timedelta(days=15)

        # Get custom post-hire reminder activity type
        activity_type = self.env.ref('recruitment_management.mail_activity_type_post_hire_reminder', raise_if_not_found=False)
        if not activity_type:
            # Fallback to default "To Do"
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            # Last resort fallback
            activity_type = self.env['mail.activity.type'].search([], limit=1)

        # Create the activity
        activity = self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'summary': f'Post-Hire Follow-up: {self.partner_name}',
            'note': f"""
                <p><strong>15-Day Post-Hire Reminder</strong></p>
                <p>Follow up with the hired candidate: <strong>{self.partner_name}</strong></p>
                <p><strong>Job Position:</strong> {self.job_id.name if self.job_id else 'N/A'}</p>
                <p><strong>Contract Salary:</strong> {self.contract_salary if self.contract_salary else 'Not specified'}</p>
                <hr/>
                <p><strong>Action Items:</strong></p>
                <ul>
                    <li>Check candidate's onboarding progress</li>
                    <li>Verify contract signing status</li>
                    <li>Confirm start date and first day arrangements</li>
                    <li>Schedule initial performance check-in</li>
                </ul>
            """,
            'date_deadline': reminder_date,
            'res_model_id': self.env['ir.model']._get_id('hr.applicant'),
            'res_id': self.id,
            'user_id': self.user_id.id if self.user_id else self.env.user.id,
        })

        # Log message on the applicant
        self.message_post(
            body=f"""
                <p><strong>Post-Hire Reminder Created</strong></p>
                <p>A follow-up activity has been scheduled for {reminder_date.strftime('%B %d, %Y')}
                (15 days from hire date) to check on the candidate's onboarding progress.</p>
            """,
            subject='Post-Hire Reminder Scheduled'
        )
