# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BCWorkerSkill(models.Model):
    _name = 'bc.worker.skill'
    _description = 'Worker Skill'
    _order = 'name'

    name = fields.Char(string='Skill Name', required=True, translate=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)


class BCWorker(models.Model):
    _name = 'bc.worker'
    _description = 'Blue Collar Worker'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
    _order = 'name'

    # Basic Information
    name = fields.Char(string='Worker Name', required=True, tracking=True)
    ref = fields.Char(string='Reference', copy=False, readonly=True, default=lambda self: _('New'))

    partner_id = fields.Many2one('res.partner', string='Related Contact', tracking=True)
    agency_id = fields.Many2one(
        'res.partner',
        string='Related Agency',
        domain="[('is_agency', '=', True)]",
        tracking=True,
    )
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    mobile = fields.Char(string='Mobile', tracking=True)

    date_of_birth = fields.Date(string='Date of Birth', tracking=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', tracking=True)

    nationality_id = fields.Many2one('res.country', string='Nationality', tracking=True)
    country_id = fields.Many2one('res.country', string='Current Country')

    # Skills & Experience
    skill_ids = fields.Many2many('bc.worker.skill', string='Skills')
    experience_years = fields.Integer(string='Years of Experience', default=0)
    education = fields.Text(string='Education Background')

    # Documents
    passport_number = fields.Char(string='Passport Number', tracking=True)
    passport_expiry = fields.Date(string='Passport Expiry Date', tracking=True)
    passport_copy = fields.Binary(string='Passport Copy', attachment=True)
    passport_filename = fields.Char(string='Passport Filename')

    visa_number = fields.Char(string='Visa Number', tracking=True)
    visa_expiry = fields.Date(string='Visa Expiry Date', tracking=True)
    visa_copy = fields.Binary(string='Visa Copy', attachment=True)
    visa_filename = fields.Char(string='Visa Filename')

    work_permit_number = fields.Char(string='Work Permit Number')
    work_permit_expiry = fields.Date(string='Work Permit Expiry')
    work_permit_copy = fields.Binary(string='Work Permit Copy', attachment=True)
    work_permit_filename = fields.Char(string='Work Permit Filename')

    medical_certificate = fields.Binary(string='Medical Certificate', attachment=True)
    medical_certificate_filename = fields.Char(string='Medical Certificate Filename')
    medical_certificate_expiry = fields.Date(string='Medical Certificate Expiry')

    resume = fields.Binary(string='CV/Resume', attachment=True)
    resume_filename = fields.Char(string='CV Filename')

    # Availability & Status
    availability_status = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('on_leave', 'On Leave'),
        ('unavailable', 'Unavailable'),
        ('terminated', 'Terminated')
    ], string='Availability Status', default='available', required=True, tracking=True)

    available_from = fields.Date(string='Available From')

    # Placements
    placement_ids = fields.One2many('bc.placement', 'worker_id', string='Placements')
    placement_count = fields.Integer(string='Total Placements', compute='_compute_placement_count', store=True)
    current_placement_id = fields.Many2one('bc.placement', string='Current Placement',
                                          compute='_compute_current_placement', store=True)

    # Financial
    expected_salary = fields.Monetary(string='Expected Salary', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    # Other
    notes = fields.Text(string='Internal Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)

    # Constraints
    _sql_constraints = [
        ('passport_unique', 'unique(passport_number)', 'Passport number must be unique!'),
    ]

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.today()
        for worker in self:
            if worker.date_of_birth:
                worker.age = (today - worker.date_of_birth).days // 365
            else:
                worker.age = 0

    @api.depends('placement_ids')
    def _compute_placement_count(self):
        for worker in self:
            worker.placement_count = len(worker.placement_ids)

    @api.depends('placement_ids', 'placement_ids.state')
    def _compute_current_placement(self):
        for worker in self:
            current = worker.placement_ids.filtered(lambda p: p.state in ['assigned', 'active'])
            worker.current_placement_id = current[0] if current else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', _('New')) == _('New'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('bc.worker') or _('New')
        return super().create(vals_list)

    def action_view_placements(self):
        """View all placements for this worker"""
        self.ensure_one()
        return {
            'name': _('Worker Placements'),
            'type': 'ir.actions.act_window',
            'res_model': 'bc.placement',
            'view_mode': 'list,form',
            'domain': [('worker_id', '=', self.id)],
            'context': {'default_worker_id': self.id}
        }

    def action_set_available(self):
        """Set worker as available"""
        self.write({'availability_status': 'available'})

    def action_set_unavailable(self):
        """Set worker as unavailable"""
        self.write({'availability_status': 'unavailable'})

    def unlink(self):
        """Prevent deletion of workers with active placements"""
        for worker in self:
            if worker.placement_ids.filtered(lambda p: p.state in ['assigned', 'active']):
                raise ValidationError(_('Cannot delete worker %s with active placements. Please terminate placements first.') % worker.name)
        return super().unlink()

    @api.constrains('passport_expiry', 'visa_expiry', 'work_permit_expiry')
    def _check_document_expiry(self):
        """Check if documents are expired"""
        today = fields.Date.today()
        for worker in self:
            if worker.passport_expiry and worker.passport_expiry < today:
                raise ValidationError(_('Passport for %s has expired!') % worker.name)
            if worker.visa_expiry and worker.visa_expiry < today:
                raise ValidationError(_('Visa for %s has expired!') % worker.name)
            if worker.work_permit_expiry and worker.work_permit_expiry < today:
                raise ValidationError(_('Work permit for %s has expired!') % worker.name)
