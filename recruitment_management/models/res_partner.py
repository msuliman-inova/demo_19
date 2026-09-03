from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    job_ids = fields.One2many("hr.job",  "partner_id", string="Jobs")
    user_type = fields.Selection([
            ('employee', 'Employee (Job Seeker)'),
            ('employer', 'Employer (Hiring)'),
            ('other', 'Other')],
        string='User Type',
        default='other',
        help='Type of portal user'
    )

    def action_open_jobs(self):
        return {
                'type': 'ir.actions.act_window',
                'name': 'Jobs',
                'res_model': 'hr.job',
                'view_mode': 'list,form',
                'domain': [('id', 'in', self.job_ids.ids)],
                'target': 'current',
                }

    @api.model
    def _get_signup_fields(self):
        """Add user_type to signup fields"""
        res = super()._get_signup_fields()
        if 'user_type' not in res:
            res.append('user_type')
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to grant portal access for employers"""
        partners = super(ResPartner, self).create(vals_list)

        # Skip automatic portal creation if user is being created from the backend
        # or if context indicates we should skip it
        if self.env.context.get('skip_portal_creation') or self.env.context.get('no_reset_password'):
            return partners

        for partner in partners:
            # Only process if user_type is employer and has email
            # Also check that partner doesn't already have a user (prevents conflict during user creation)
            if partner.user_type == 'employer' and partner.email and not partner.user_ids:
                # Create portal user with recruitment portal group
                try:
                    portal_wizard = self.env['portal.wizard'].sudo().create({
                        'user_ids': [(0, 0, {
                            'partner_id': partner.id,
                            'email': partner.email,
                        })]
                    })
                    portal_wizard.user_ids.action_grant_access()

                    # Reload partner to get the newly created user
                    partner.invalidate_recordset(['user_ids'])
                    user = partner.user_ids and partner.user_ids[0] or False

                    # Add recruitment portal group
                    if user:
                        group = self.env.ref('recruitment_management.group_recruitment_portal', raise_if_not_found=False)
                        if group:
                            group.sudo().write({'user_ids': [(4, user.id)]})
                except Exception:
                    # Silently fail - don't block partner creation
                    pass

        return partners

    def write(self, vals):
        """Override write to grant portal access when user_type or email changes to employer"""
        res = super(ResPartner, self).write(vals)

        # Skip automatic portal creation if context indicates we should skip it
        if self.env.context.get('skip_portal_creation') or self.env.context.get('no_reset_password'):
            return res

        # Check if user_type changed to employer or email was added
        if 'user_type' in vals or 'email' in vals:
            for partner in self:
                # Only process if user_type is employer, has email, and no user yet
                if partner.user_type == 'employer' and partner.email and not partner.user_ids:
                    # Create portal user with recruitment portal group
                    try:
                        portal_wizard = self.env['portal.wizard'].sudo().create({
                            'user_ids': [(0, 0, {
                                'partner_id': partner.id,
                                'email': partner.email,
                            })]
                        })
                        portal_wizard.user_ids.action_grant_access()

                        # Reload partner to get the newly created user
                        partner.invalidate_recordset(['user_ids'])
                        user = partner.user_ids and partner.user_ids[0] or False

                        # Add recruitment portal group
                        if user:
                            group = self.env.ref('recruitment_management.group_recruitment_portal', raise_if_not_found=False)
                            if group:
                                group.sudo().write({'user_ids': [(4, user.id)]})
                    except Exception:
                        # Silently fail - don't block partner update
                        pass

        return res


    recruitment_request_ids = fields.One2many(
        'recruitment.request',
        'partner_id',
        string='Recruitment Requests'
    )

    recruitment_request_count = fields.Integer(
        string='Request Count',
        compute='_compute_recruitment_request_count'
    )

    @api.depends('recruitment_request_ids')
    def _compute_recruitment_request_count(self):
        for partner in self:
            partner.recruitment_request_count = len(partner.recruitment_request_ids)

    def action_view_recruitment_requests(self):
        """View all recruitment requests for this partner"""
        self.ensure_one()
        return {
            'name': _('Recruitment Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'recruitment.request',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }
