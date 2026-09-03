from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RecruitmentUrgencyConfig(models.Model):
    _name = 'recruitment.urgency.config'
    _description = 'Recruitment Urgency Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Configuration Name', default='Urgency Settings', readonly=True)

    # Urgency Threshold Settings
    urgency_attention_days = fields.Integer(
        string='Attention Threshold (Days)',
        default=7,
        required=True,
        help='Number of days remaining to trigger "Needs Attention" status'
    )

    urgency_urgent_days = fields.Integer(
        string='Urgent Threshold (Days)',
        default=3,
        required=True,
        help='Number of days remaining to trigger "Urgent" status (Orange)'
    )

    active = fields.Boolean(string='Active', default=True)

    @api.constrains('urgency_attention_days', 'urgency_urgent_days')
    def _check_urgency_days(self):
        """Ensure attention days is greater than urgent days"""
        for record in self:
            if record.urgency_urgent_days >= record.urgency_attention_days:
                raise ValidationError(
                    'Attention threshold must be greater than Urgent threshold. '
                    f'Current: Urgent={record.urgency_urgent_days}, Attention={record.urgency_attention_days}'
                )

    @api.model
    def get_config(self):
        """Get the active configuration or create default one"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            config = self.create({
                'name': 'Urgency Settings',
                'urgency_urgent_days': 3,
                'urgency_attention_days': 7,
            })
        return config

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure only one active config exists"""
        for vals in vals_list:
            if vals.get('active', True):
                # Deactivate all other configs
                self.search([]).write({'active': False})
                break
        return super().create(vals_list)

    def write(self, vals):
        """Ensure only one active config exists"""
        if vals.get('active', False):
            # Deactivate all other configs
            self.search([('id', '!=', self.id)]).write({'active': False})
        return super().write(vals)
