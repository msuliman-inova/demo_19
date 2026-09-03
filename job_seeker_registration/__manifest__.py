{
    'name': 'Job Seeker Registration',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Recruitment',
    'summary': 'Job seeker registration system for future vacancy notifications',
    'description': """
        Job Seeker Registration
        ============================

        Allows job seekers to register their interest when no suitable positions are available:
        * Register job seeker data from website /jobs page
        * Store seeker information for future vacancies
        * Notify seekers when matching positions become available
        * Convert registrations to job applications with one click
        * Track seeker status and communication history
    """,
    'author': 'Haidab Smart Solution',
    'website': 'https://haidabsmart.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr_recruitment',
        'website',
        'mail',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/job_seeker_data.xml',

        # Views
        'views/job_seeker_registration_views.xml',
        'views/job_seeker_convert_wizard_views.xml',
        'views/website_jobs_template.xml',
        'views/recruitment_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence':-3,
}
