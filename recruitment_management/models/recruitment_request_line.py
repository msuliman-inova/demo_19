from odoo import api, fields, models, _


class RecruitmentRequestLine(models.Model):
    _name = 'recruitment.request.line'
    _description = 'Recruitment Request Job Line'
    _order = 'sequence, id'

    request_id = fields.Many2one(
        'recruitment.request',
        string='Recruitment Request',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)

    # Job Details
    job_title = fields.Char(
        string='Job Title',
        required=True
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department'
    )

    no_of_positions = fields.Integer(
        string='Number of Positions',
        default=1,
        required=True
    )

    emp_contract_type = fields.Many2one(
        'hr.contract.type',
        string='Contract Type',
        required=True
    )

    # Requirements
    job_description = fields.Html(
        string='Job Description'
    )

    requirements = fields.Html(
        string='Requirements & Qualifications'
    )

    expected_degree = fields.Many2one(
        'hr.recruitment.degree',
        string='Minimum Education Level'
    )

    job_skill_ids = fields.Many2many(
        comodel_name='hr.skill',
        relation='recruitment_line_skill_rel',
        column1='line_id',
        column2='skill_id',
        string='Skills'
    )

    experience_years = fields.Integer(
        string='Required Experience (Years)',
        default=0
    )

    # Compensation
    salary_from = fields.Monetary(
        string='Salary From',
        currency_field='currency_id'
    )

    salary_to = fields.Monetary(
        string='Salary To',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='request_id.currency_id',
        store=True
    )

    # Pricing - Simplified as per requirement
    pricing_percentage = fields.Float(
        string='Fee Percentage (%)',
        default=8.33,
        help='Fee percentage (default 8.33%)'
    )

    # service_fee field removed as per requirement
    # service_fee = fields.Monetary(
    #     string='Service Fee',
    #     currency_field='currency_id',
    #     compute='_compute_service_fee_from_percentage',
    #     store=True,
    #     readonly=False
    # )

    # Related Job Position
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        readonly=True,
        copy=False
    )

    # Pricing calculation methods - Commented out as per requirement
    # @api.depends('no_of_positions', 'emp_contract_type', 'experience_years', 'salary_from', 'salary_to')
    # def _compute_service_fee(self):
    #     """Calculate percentage based on pricing rules and salary range"""
    #     for line in self:
    #         # Skip if percentage was manually set
    #         if line._origin and line._origin.pricing_percentage and line.pricing_percentage != line._origin.pricing_percentage:
    #             continue
    #
    #         line.pricing_percentage = 0.0
    #
    #         # Skip if no contract type or positions
    #         if not line.emp_contract_type or not line.no_of_positions:
    #             continue
    #
    #         # Calculate average salary for matching
    #         avg_salary = 0.0
    #         if line.salary_from and line.salary_to:
    #             avg_salary = (line.salary_from + line.salary_to) / 2
    #         elif line.salary_from:
    #             avg_salary = line.salary_from
    #         elif line.salary_to:
    #             avg_salary = line.salary_to
    #
    #         # Skip if no salary defined
    #         if not avg_salary:
    #             continue
    #
    #         # Search for pricing rule based on contract type and salary range
    #         pricing = self.env['recruitment.pricing'].search([
    #             ('emp_contract_type', '=', line.emp_contract_type.id),
    #             ('min_salary', '<=', avg_salary),
    #             ('max_salary', '>=', avg_salary),
    #             ('active', '=', True),
    #         ], limit=1)
    #
    #         if pricing and pricing.percentage > 0:
    #             # Store the percentage used
    #             line.pricing_percentage = pricing.percentage
    #
    # @api.depends('pricing_percentage', 'no_of_positions', 'salary_from', 'salary_to')
    # def _compute_service_fee_from_percentage(self):
    #     """Calculate service fee based on percentage"""
    #     for line in self:
    #         line.service_fee = 0.0
    #
    #         # Skip if no percentage or positions
    #         if not line.pricing_percentage or not line.no_of_positions:
    #             continue
    #
    #         # Calculate average salary
    #         avg_salary = 0.0
    #         if line.salary_from and line.salary_to:
    #             avg_salary = (line.salary_from + line.salary_to) / 2
    #         elif line.salary_from:
    #             avg_salary = line.salary_from
    #         elif line.salary_to:
    #             avg_salary = line.salary_to
    #
    #         # Skip if no salary defined
    #         if not avg_salary:
    #             continue
    #
    #         # Calculate fee based on percentage of average salary * no_of_positions
    #         line.service_fee = (avg_salary * line.pricing_percentage / 100.0) * line.no_of_positions
    #
    # @api.onchange('no_of_positions', 'salary_from', 'salary_to', 'emp_contract_type', 'experience_years')
    # def _onchange_compute_service_fee(self):
    #     """Trigger service fee computation on field changes"""
    #     self._compute_service_fee()
    #     self._compute_service_fee_from_percentage()
    #
    # @api.onchange('pricing_percentage')
    # def _onchange_pricing_percentage(self):
    #     """Recalculate service fee when percentage changes"""
    #     self._compute_service_fee_from_percentage()
    #
    # def write(self, vals):
    #     """Override write to update related sale order lines"""
    #     res = super(RecruitmentRequestLine, self).write(vals)
    #
    #     # If percentage or fee changed, update related quotations
    #     if 'pricing_percentage' in vals or 'service_fee' in vals or 'no_of_positions' in vals:
    #         for line in self:
    #             if line.request_id.sale_order_id and line.request_id.sale_order_id.state in ['draft', 'sent']:
    #                 # Update sale order lines
    #                 line._update_sale_order_lines()
    #
    #     return res
    #
    # def _update_sale_order_lines(self):
    #     """Update related sale order lines with new values"""
    #     self.ensure_one()
    #
    #     if not self.request_id.sale_order_id:
    #         return
    #
    #     sale_order = self.request_id.sale_order_id
    #
    #     # Find matching sale order line by job title in description
    #     for so_line in sale_order.order_line:
    #         if so_line.name and self.job_title in so_line.name:
    #             # Calculate new values
    #             avg_salary = 0.0
    #             if self.salary_from and self.salary_to:
    #                 avg_salary = (self.salary_from + self.salary_to) / 2
    #             elif self.salary_from:
    #                 avg_salary = self.salary_from
    #             elif self.salary_to:
    #                 avg_salary = self.salary_to
    #
    #             # Build updated description
    #             description = _('Recruitment Service: %s') % self.job_title
    #             if self.pricing_percentage > 0 and avg_salary > 0:
    #                 description += _('\nSalary Range: %s - %s (Avg: %s)') % (
    #                     '{:,.2f}'.format(self.salary_from) if self.salary_from else 'N/A',
    #                     '{:,.2f}'.format(self.salary_to) if self.salary_to else 'N/A',
    #                     '{:,.2f}'.format(avg_salary)
    #                 )
    #                 description += _('\nFee Percentage: %s%%') % self.pricing_percentage
    #
    #             # Update sale order line
    #             so_line.write({
    #                 'name': description,
    #                 'product_uom_qty': self.no_of_positions,
    #                 'price_unit': self.service_fee / self.no_of_positions if self.no_of_positions else 0,
    #                 'recruitment_percentage': self.pricing_percentage,
    #             })
    #             break

    # Helper fields for skill selection (same as parent)
    skill_type_id = fields.Many2one(
        'hr.skill.type',
        string='Skill Category',
        help='Filter skills by category'
    )
    skill_id = fields.Many2one(
        'hr.skill',
        string='Skill',
        domain="[('skill_type_id', '=', skill_type_id)]"
    )

    def action_add_skill(self):
        """Add selected skill to job_skill_ids"""
        self.ensure_one()
        if self.skill_id:
            if self.skill_id not in self.job_skill_ids:
                self.job_skill_ids = [(4, self.skill_id.id)]
            # Clear selection fields
            self.skill_type_id = False
            self.skill_id = False
        return {'type': 'ir.actions.act_window_close'}

    def action_open_form(self):
        """Open form view for this job line"""
        self.ensure_one()
        return {
            'name': _('Job Line - %s') % self.job_title,
            'type': 'ir.actions.act_window',
            'res_model': 'recruitment.request.line',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',  # Open in dialog
            'context': self.env.context,
        }
