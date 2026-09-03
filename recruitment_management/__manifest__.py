{
    'name': 'Recruitment Management',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Recruitment',
    'summary': 'Integrated recruitment request management system with CRM, Sales and Portal',
    'description': """
        Recruitment Management System
        ==================================

        Complete recruitment request management system that integrates:
        * Employer portal for job requests
        * CRM integration for lead management
        * Automatic quotation generation
        * Recruitment job position creation
        * Sales order and invoicing
        * Multi-stage approval workflow

        Features:
        ---------
        * Employer self-service portal
        * Automated workflow from request to hire
        * Dynamic pricing based on job requirements
        * Integration with accounting for invoicing
        * Comprehensive reporting and analytics
        * Interview recording management with Google Drive integration
    """,
    'author': 'Haidab Smart Solution',
    'website': 'https://haidabsmart.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'hr_recruitment',
        'hr_recruitment_integration_base',
        'hr_skills',
        'portal',
        'auth_signup',
        'sale_management',
        'sale_crm',
        'account',
        'mail',
        'web',
        'website',
    ],
    'data': [
        # Security
        'security/recruitment_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/recruitment_data.xml',
        'data/contact_subject_data.xml',
        'data/recruitment_urgency_config_data.xml',
        'data/mail_template_data.xml',
        'data/mail_activity_type_data.xml',
        'data/ir_sequence_data.xml',

        # Wizards (must load before views that reference them)
        'wizards/recruitment_quotation_wizard_views.xml',
        'wizards/convert_to_recruitment_wizard_views.xml',
        'wizards/crm_lead_to_opportunity_views.xml',
        'wizards/stage_change_confirm_wizard_views.xml',

        # Views
        'views/recruitment_request_views.xml',
        'views/recruitment_request_line_views.xml',
        'views/contact_subject_views.xml',
        'views/hr_job_views.xml',
        'views/hr_recruitment_stage_views.xml',
        'views/hr_applicant_views.xml',
        'views/res_partner_views.xml',
        'views/recruitment_urgency_config_views.xml',
        'views/sale_order.xml',
        'views/website_contactus_template.xml',
        'views/crm_lead_views.xml',
        'views/crm_stage_views.xml',

        # Portal
        'views/portal_recruitment_request_templates.xml',
        'views/portal_recruitment_form_wizard.xml',
        'views/portal_quick_submit_form.xml',
        'views/portal_form_mode_toggle.xml',
        'views/portal_signup_templates.xml',
        'views/portal_sale_order_templates.xml',
        'views/portal_interview_templates.xml',
        'views/recruitment_menus.xml',
        # Reports
        'reports/sale_order_report_templates.xml',
        # 'reports/recruitment_request_report.xml',
        # 'reports/recruitment_request_templates.xml',
    ],
    'demo': [
        # 'demo/recruitment_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # 'recruitment_management/static/src/js/portal.js',
        ],
    },
    'images': [
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence':-1,
}