# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class BCDashboardWizard(models.TransientModel):
    _name = 'bc.dashboard.wizard'
    _description = 'BC Recruitment Dashboard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True, readonly=True)
    project_id = fields.Many2one('account.analytic.account', string='Project',
                                 help='If set, dashboard will show all sales and purchases for this project')

    # Sales Overview
    sale_order_ids = fields.Many2many('sale.order', string='Related Sales', compute='_compute_dashboard_data')
    total_sales_amount = fields.Monetary(string='Total Sales', compute='_compute_dashboard_data', currency_field='currency_id')
    total_invoiced_sales = fields.Monetary(string='Invoiced Sales', compute='_compute_dashboard_data', currency_field='currency_id')
    total_uninvoiced_sales = fields.Monetary(string='Uninvoiced Sales', compute='_compute_dashboard_data', currency_field='currency_id')

    # Purchase Overview
    purchase_order_ids = fields.Many2many('purchase.order', string='Related Purchases', compute='_compute_dashboard_data')
    total_purchase_amount = fields.Monetary(string='Total Purchases', compute='_compute_dashboard_data', currency_field='currency_id')
    total_invoiced_purchase = fields.Monetary(string='Invoiced Purchases', compute='_compute_dashboard_data', currency_field='currency_id')
    total_uninvoiced_purchase = fields.Monetary(string='Uninvoiced Purchases', compute='_compute_dashboard_data', currency_field='currency_id')

    # Job Orders
    job_order_ids = fields.Many2many('bc.job.order', string='Job Orders', compute='_compute_dashboard_data')
    total_positions_requested = fields.Integer(string='Total Positions', compute='_compute_dashboard_data')
    total_positions_filled = fields.Integer(string='Positions Filled', compute='_compute_dashboard_data')
    fill_rate = fields.Float(string='Fill Rate %', compute='_compute_dashboard_data')

    # Customer Invoices
    customer_invoice_ids = fields.Many2many('account.move', 'bc_dashboard_customer_invoice_rel',
                                           string='Customer Invoices', compute='_compute_dashboard_data')
    vendor_invoice_ids = fields.Many2many('account.move', 'bc_dashboard_vendor_invoice_rel',
                                         string='Vendor Bills', compute='_compute_dashboard_data')

    # Profit & Loss
    expected_margin = fields.Monetary(string='Expected Margin', compute='_compute_dashboard_data', currency_field='currency_id')
    actual_margin = fields.Monetary(string='Actual Margin (Invoiced)', compute='_compute_dashboard_data', currency_field='currency_id')
    margin_percentage = fields.Float(string='Margin %', compute='_compute_dashboard_data')

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='sale_order_id.currency_id', readonly=True)

    # Counts for smart buttons
    sales_count = fields.Integer(compute='_compute_dashboard_data')
    purchase_count = fields.Integer(compute='_compute_dashboard_data')
    job_count = fields.Integer(compute='_compute_dashboard_data')
    customer_invoice_count = fields.Integer(compute='_compute_dashboard_data')
    vendor_invoice_count = fields.Integer(compute='_compute_dashboard_data')

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Auto-populate project if sale order has one"""
        if self.sale_order_id and self.sale_order_id.order_line:
            for line in self.sale_order_id.order_line:
                # Check for analytic_distribution (Odoo 16+)
                if hasattr(line, 'analytic_distribution') and line.analytic_distribution:
                    account_ids = [int(k) for k in line.analytic_distribution.keys()]
                    if account_ids:
                        self.project_id = self.env['account.analytic.account'].browse(account_ids[0])
                        break
                # Check for analytic_account_id (older Odoo versions)
                elif hasattr(line, 'analytic_account_id') and line.analytic_account_id:
                    self.project_id = line.analytic_account_id
                    break

    @api.depends('sale_order_id', 'project_id')
    def _compute_dashboard_data(self):
        for wizard in self:
            # Get analytic accounts from sale order lines or project
            analytic_account_ids = set()

            # Priority 1: Use project_id if explicitly set
            if wizard.project_id:
                analytic_account_ids.add(wizard.project_id.id)

            # Priority 2: Collect ALL analytic accounts from current sale order lines
            if wizard.sale_order_id and wizard.sale_order_id.order_line:
                for line in wizard.sale_order_id.order_line:
                    if hasattr(line, 'analytic_distribution') and line.analytic_distribution:
                        try:
                            analytic_account_ids.update([int(k) for k in line.analytic_distribution.keys()])
                        except (ValueError, TypeError):
                            continue
                    elif hasattr(line, 'analytic_account_id') and line.analytic_account_id:
                        analytic_account_ids.add(line.analytic_account_id.id)

            # Debug: Log the analytic accounts found (can be removed later)
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info(f"Dashboard for SO {wizard.sale_order_id.name if wizard.sale_order_id else 'None'}: Found analytic accounts: {analytic_account_ids}")

            # Find all sales orders linked to the same analytic account(s)
            sales_orders = self.env['sale.order']
            job_orders = self.env['bc.job.order']
            customer_invoices = self.env['account.move']

            if wizard.project_id:
                # Find all confirmed sales orders linked to this project (regardless of BC recruitment flag)
                # Search by analytic account on order lines
                if 'analytic_distribution' in self.env['sale.order.line']._fields:
                    # Odoo 16+ with analytic_distribution
                    so_lines = self.env['sale.order.line'].search([
                        ('order_id.state', '=', 'sale')  # Only confirmed orders
                    ])
                    for line in so_lines:
                        if line.analytic_distribution:
                            try:
                                line_analytic_ids = {int(k) for k in line.analytic_distribution.keys()}
                                if wizard.project_id.id in line_analytic_ids:
                                    sales_orders |= line.order_id
                            except (ValueError, TypeError):
                                continue
                elif 'analytic_account_id' in self.env['sale.order.line']._fields:
                    # Older Odoo with analytic_account_id
                    so_lines = self.env['sale.order.line'].search([
                        ('analytic_account_id', '=', wizard.project_id.id),
                        ('order_id.state', '=', 'sale')
                    ])
                    sales_orders = so_lines.mapped('order_id')

                # Also check if sale order has direct project_id field
                if 'project_id' in self.env['sale.order']._fields:
                    direct_sos = self.env['sale.order'].search([
                        ('project_id', '=', wizard.project_id.id),
                        ('state', '=', 'sale')
                    ])
                    sales_orders |= direct_sos

                # Ensure the current sale order is always included (even if draft)
                if wizard.sale_order_id:
                    sales_orders |= wizard.sale_order_id
            else:
                # If no project selected, just use the current sale order
                sales_orders = wizard.sale_order_id

            # Debug: Log the sales orders found
            _logger.info(f"Dashboard: Found {len(sales_orders)} sales orders: {sales_orders.mapped('name')}")

            # Sales data
            wizard.sale_order_ids = sales_orders
            wizard.job_order_ids = sales_orders.mapped('job_order_ids')

            # Get all customer invoices from all related sale orders
            for so in sales_orders:
                customer_invoices |= so.invoice_ids.filtered(
                    lambda inv: inv.move_type == 'out_invoice' and inv.state != 'cancel'
                )
            wizard.customer_invoice_ids = customer_invoices

            # Sales amounts (from all related sale orders) - excluding taxes
            wizard.total_sales_amount = sum(sales_orders.mapped('amount_untaxed'))
            wizard.total_invoiced_sales = sum(customer_invoices.filtered(
                lambda inv: inv.state == 'posted').mapped('amount_untaxed'))
            wizard.total_uninvoiced_sales = wizard.total_sales_amount - wizard.total_invoiced_sales

            # Find purchase orders and vendor bills by project
            purchases = self.env['purchase.order']
            vendor_bills = self.env['account.move']

            if wizard.project_id:
                # Search for purchase orders linked to this project
                if 'analytic_distribution' in self.env['purchase.order.line']._fields:
                    # Odoo 16+ with analytic_distribution
                    all_po_lines = self.env['purchase.order.line'].search([])
                    for line in all_po_lines:
                        if line.analytic_distribution:
                            try:
                                line_analytic_ids = {int(k) for k in line.analytic_distribution.keys()}
                                if wizard.project_id.id in line_analytic_ids:
                                    purchases |= line.order_id
                            except (ValueError, TypeError):
                                continue
                elif 'analytic_account_id' in self.env['purchase.order.line']._fields:
                    # Older Odoo with analytic_account_id
                    po_lines = self.env['purchase.order.line'].search([
                        ('analytic_account_id', '=', wizard.project_id.id)
                    ])
                    purchases = po_lines.mapped('order_id')

                # Search for vendor bills linked to this project
                if 'analytic_distribution' in self.env['account.move.line']._fields:
                    # Odoo 16+ with analytic_distribution
                    all_bill_lines = self.env['account.move.line'].search([
                        ('move_id.move_type', '=', 'in_invoice'),
                        ('move_id.state', '!=', 'cancel'),
                        ('display_type', 'not in', ['line_section', 'line_note'])
                    ])
                    for line in all_bill_lines:
                        if line.analytic_distribution:
                            try:
                                line_analytic_ids = {int(k) for k in line.analytic_distribution.keys()}
                                if wizard.project_id.id in line_analytic_ids:
                                    vendor_bills |= line.move_id
                            except (ValueError, TypeError):
                                continue
                elif 'analytic_account_id' in self.env['account.move.line']._fields:
                    # Older Odoo with analytic_account_id
                    bill_lines = self.env['account.move.line'].search([
                        ('move_id.move_type', '=', 'in_invoice'),
                        ('move_id.state', '!=', 'cancel'),
                        ('display_type', 'not in', ['line_section', 'line_note']),
                        ('analytic_account_id', '=', wizard.project_id.id)
                    ])
                    vendor_bills = bill_lines.mapped('move_id')

            wizard.purchase_order_ids = purchases
            wizard.vendor_invoice_ids = vendor_bills

            # Purchase amounts - excluding taxes
            wizard.total_purchase_amount = sum(purchases.mapped('amount_untaxed'))
            wizard.total_invoiced_purchase = sum(vendor_bills.filtered(
                lambda inv: inv.state == 'posted').mapped('amount_untaxed'))
            wizard.total_uninvoiced_purchase = wizard.total_purchase_amount - wizard.total_invoiced_purchase

            # Job order stats
            wizard.total_positions_requested = sum(wizard.job_order_ids.mapped('positions_requested'))
            wizard.total_positions_filled = sum(wizard.job_order_ids.mapped('positions_filled'))

            # Calculate fill rate as decimal for percentage widget
            if wizard.total_positions_requested > 0:
                wizard.fill_rate = wizard.total_positions_filled / wizard.total_positions_requested
            else:
                wizard.fill_rate = 0

            # Profit & Loss calculations
            wizard.expected_margin = wizard.total_sales_amount - wizard.total_purchase_amount
            wizard.actual_margin = wizard.total_invoiced_sales - wizard.total_invoiced_purchase

            # Margin percentage based on invoiced sales (actual margin)
            # Store as decimal for percentage widget (e.g., 0.58 = 58%)
            if wizard.total_invoiced_sales > 0:
                wizard.margin_percentage = wizard.actual_margin / wizard.total_invoiced_sales
            else:
                wizard.margin_percentage = 0

            # Counts
            wizard.sales_count = len(wizard.sale_order_ids)
            wizard.purchase_count = len(wizard.purchase_order_ids)
            wizard.job_count = len(wizard.job_order_ids)
            wizard.customer_invoice_count = len(wizard.customer_invoice_ids)
            wizard.vendor_invoice_count = len(wizard.vendor_invoice_ids)

    def action_view_sales(self):
        """View all related sales orders"""
        self.ensure_one()
        return {
            'name': _('Sales Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sale_order_ids.ids)],
        }

    def action_view_purchases(self):
        """View all related purchase orders"""
        self.ensure_one()
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
        }

    def action_view_jobs(self):
        """View all job orders"""
        self.ensure_one()
        return {
            'name': _('Job Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'bc.job.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.job_order_ids.ids)],
        }

    def action_view_customer_invoices(self):
        """View customer invoices"""
        self.ensure_one()
        return {
            'name': _('Customer Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.customer_invoice_ids.ids)],
        }

    def action_view_vendor_bills(self):
        """View vendor bills"""
        self.ensure_one()
        return {
            'name': _('Vendor Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.vendor_invoice_ids.ids)],
        }
