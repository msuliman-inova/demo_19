from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RecruitmentQuotationWizard(models.TransientModel):
    _name = 'recruitment.quotation.wizard'
    _description = 'Send Quotation for Recruitment Request'

    request_id = fields.Many2one(
        'recruitment.request',
        string='Recruitment Request',
        required=True,
        readonly=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        readonly=True
    )

    service_fee = fields.Monetary(
        string='Service Fee',
        currency_field='currency_id',
        required=True
    )

    additional_services = fields.Many2many(
        'recruitment.additional.service',
        string='Additional Services'
    )

    additional_fee = fields.Monetary(
        string='Additional Services Fee',
        currency_field='currency_id',
        compute='_compute_additional_fee',
        store=True
    )

    discount_percentage = fields.Float(
        string='Discount (%)',
        default=0.0
    )

    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True
    )

    discount_amount = fields.Monetary(
        string='Discount Amount',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True
    )

    final_amount = fields.Monetary(
        string='Final Amount',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    validity_days = fields.Integer(
        string='Quotation Validity (Days)',
        default=30
    )

    send_email = fields.Boolean(
        string='Send by Email',
        default=True
    )

    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain="[('model', '=', 'recruitment.request')]"
    )

    notes = fields.Text(
        string='Additional Notes'
    )

    @api.model
    def default_get(self, fields_list):
        res = super(RecruitmentQuotationWizard, self).default_get(fields_list)

        if self._context.get('default_request_id'):
            request = self.env['recruitment.request'].browse(self._context['default_request_id'])

            res.update({
                'service_fee': request.service_fee,
                'additional_services': [(6, 0, request.additional_services.ids)],
                'discount_percentage': request.discount_percentage,
            })

            # Set default email template
            template = self.env.ref('recruitment_management.email_template_quotation', raise_if_not_found=False)
            if template:
                res['email_template_id'] = template.id

        return res

    @api.depends('additional_services', 'additional_services.price')
    def _compute_additional_fee(self):
        for wizard in self:
            wizard.additional_fee = sum(wizard.additional_services.mapped('price'))

    @api.depends('service_fee', 'additional_fee', 'discount_percentage')
    def _compute_total_amount(self):
        for wizard in self:
            wizard.total_amount = wizard.service_fee + wizard.additional_fee
            wizard.discount_amount = wizard.total_amount * (wizard.discount_percentage / 100)
            wizard.final_amount = wizard.total_amount - wizard.discount_amount

    def action_send_quotation(self):
        """Create quotation (sale order) and send to customer"""
        self.ensure_one()

        if not self.final_amount:
            raise UserError(_('Total amount cannot be zero.'))

        if not self.request_id.line_ids:
            raise UserError(_('No recruitment lines found to create quotation.'))

        # Get recruitment service product
        recruitment_product = self.env.ref('recruitment_management.product_recruitment_service', raise_if_not_found=False)
        if not recruitment_product:
            raise UserError(_('Recruitment service product not found. Please check module data.'))

        # Prepare sale order lines from recruitment request lines
        order_lines = []
        for line in self.request_id.line_ids:
            if line.service_fee > 0:
                line_vals = {
                    'product_id': recruitment_product.id,
                    'name': _('Recruitment Service: %s') % line.job_title,
                    'product_uom_qty': line.no_of_positions,
                    'price_unit': line.service_fee / line.no_of_positions if line.no_of_positions else 0,
                    'product_uom': recruitment_product.uom_id.id,
                }
                order_lines.append((0, 0, line_vals))

        # Add additional services as separate order lines
        for service in self.additional_services:
            if service.price > 0:
                service_line_vals = {
                    'product_id': service.product_id.id,
                    'name': service.name,
                    'product_uom_qty': 1,
                    'price_unit': service.price,
                    'product_uom': service.product_id.uom_id.id,
                }
                order_lines.append((0, 0, service_line_vals))

        if not order_lines:
            raise UserError(_('No valid lines to create quotation.'))

        # Create Sale Order (Quotation)
        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.request_id.user_id.id if self.request_id.user_id else self.env.user.id,
            'origin': self.request_id.name,
            'recruitment_request_id': self.request_id.id,
            'order_line': order_lines,
            'validity_date': fields.Date.today() + fields.timedelta(days=self.validity_days),
            'note': self.notes,
        }

        sale_order = self.env['sale.order'].create(sale_order_vals)

        # Update request with quotation details
        self.request_id.write({
            'service_fee': self.service_fee,
            'additional_services': [(6, 0, self.additional_services.ids)],
            'discount_percentage': self.discount_percentage,
            'state': 'quotation_sent',
            'sale_order_id': sale_order.id,
        })

        # Update CRM lead with expected revenue
        if self.request_id.lead_id:
            self.request_id.lead_id.write({
                'expected_revenue': self.final_amount,
            })

        # Send email if requested
        if self.send_email and self.email_template_id:
            self.email_template_id.send_mail(
                self.request_id.id,
                force_send=True,
                email_values={
                    'email_to': self.partner_id.email,
                }
            )

        # Post message
        message = _('Quotation created: %s<br/>Total Amount: %.2f %s') % (
            sale_order.name,
            self.final_amount,
            self.currency_id.name
        )
        if self.notes:
            message += '<br/><br/>' + self.notes

        self.request_id.message_post(
            body=message,
            subject=_('Quotation Created and Sent')
        )

        # Return action to open the created quotation
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quotation'),
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }