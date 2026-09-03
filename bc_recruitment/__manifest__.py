{
    'name': 'Blue Collar Recruitment',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Recruitment',
    'summary': 'Blue collar worker recruitment and placement management',
    'description': """
        Blue Collar Recruitment Management
        ===================================

        Complete blue collar recruitment system that manages:
        * Worker pool with documents and skills
        * Job orders from client requests
        * Worker placements and assignments
        * Integration with CRM and Sales
        * Automated workflow from lead to placement

        Features:
        ---------
        * Worker database with document management
        * Job order tracking linked to sale orders
        * Placement management with fill rate tracking
        * Skill matching and availability
        * Automated invoicing on placements
    """,
    'author': 'Haidab Smart Solution',
    'website': 'https://haidabsmart.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'sale_management',
        'sale_crm',
        'sale_project',  # Required for automatic project and analytic account creation
        'account',
        'analytic',
        'project',
        'mail',
        'hr',
        'contacts',
        'recruitment_management',
    ],
    'data': [
        # Security
        'security/bc_recruitment_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/ir_sequence_data.xml',
        'data/bc_worker_skill_data.xml',

        # Wizards
        'wizards/job_order_complete_wizard_views.xml',
        'wizards/bc_dashboard_wizard_views.xml',

        # Views
        'views/bc_worker_views.xml',
        'views/bc_job_order_views.xml',
        'views/bc_placement_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': -2,
}
