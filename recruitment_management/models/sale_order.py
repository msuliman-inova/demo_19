from odoo import api, fields, models, _

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    fee_percentage = fields.Float(
        string='Fee Percentage',
        help='Fee percentage for this recruitment service'
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    recruitment_request_id = fields.Many2one(
        'recruitment.request',
        string='Recruitment Request',
        readonly=True
    )

    is_recruitment_order = fields.Boolean(
        string='Is Recruitment Order',
        compute='_compute_is_recruitment_order',
        store=True
    )

    recruitment_invoicing_policy = fields.Selection(
        string='Recruitment Invoicing Policy',
        related='recruitment_request_id.invoicing_policy',
        store=False
    )

    show_prices = fields.Boolean(
        string='Show Prices in Portal',
        default=False,
        help='Enable to display prices, taxes, and totals in the portal quotation view'
    )

    @api.depends('recruitment_request_id')
    def _compute_is_recruitment_order(self):
        for order in self:
            order.is_recruitment_order = bool(order.recruitment_request_id)

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

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to link sale order to recruitment request and CRM lead"""
        orders = super(SaleOrder, self).create(vals_list)
        for order in orders:
            # Link via recruitment_request_id or via opportunity's recruitment request
            rec_request = order.recruitment_request_id
            if not rec_request and order.opportunity_id and order.opportunity_id.recruitment_request_id:
                rec_request = order.opportunity_id.recruitment_request_id
                order.recruitment_request_id = rec_request

            if rec_request:
                vals = {'sale_order_id': order.id}
                if rec_request.state in ('draft', 'submitted', 'under_review'):
                    vals['state'] = 'quotation_sent'
                rec_request.write(vals)

                # Update CRM lead if exists
                if rec_request.lead_id:
                    rec_request.lead_id.write({
                        'expected_revenue': order.amount_total,
                    })
        return orders

    def action_quotation_send(self):
        """Override send quotation to update recruitment request state"""
        res = super(SaleOrder, self).action_quotation_send()
        for order in self:
            if order.recruitment_request_id and order.recruitment_request_id.state != 'quotation_sent':
                order.recruitment_request_id.write({
                    'state': 'quotation_sent',
                    'sale_order_id': order.id
                })
        return res

    def action_confirm(self):
        """Override to update recruitment request state on confirmation"""
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            rec_request = order.recruitment_request_id
            if not rec_request and order.opportunity_id and order.opportunity_id.recruitment_request_id:
                rec_request = order.opportunity_id.recruitment_request_id
                order.recruitment_request_id = rec_request
                if not rec_request.sale_order_id:
                    rec_request.sale_order_id = order.id

            if rec_request and rec_request.state in ('draft', 'quotation_sent'):
                rec_request.write({'state': 'approved'})
        return res
