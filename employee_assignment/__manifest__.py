{
    'name': 'Employee Assignment Tracking',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Track assigned employee for shared user accounts in CRM, Sales, and Invoices',
    'description': """
        Employee Assignment Tracking
        =============================

        This module allows multiple employees sharing the same Odoo user account
        to track which employee is assigned to/working on each record in:

        * CRM Leads/Opportunities
        * Sales Orders
        * Invoices (Account Moves)

        Features:
        ---------
        * Adds "Assigned Employee" field to CRM, Sales, and Invoices
        * Automatically sets current user's employee as default
        * Allows easy switching between employees
        * Filters and grouping by assigned employee
    """,
    'author': 'Haidab Smart Solution',
    'website': 'https://haidabsmart.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'sale_management',
        'account',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
