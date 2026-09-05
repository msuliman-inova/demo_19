{
    'name': 'Inova Technology - Report Layouts',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Custom report layouts for Inova Technology: Proforma Invoice and Tax Invoice enhancements',
    'author': 'Inova Technology',
    'website': 'https://inova.technology',
    'maintainer': 'Inova Technology',
    'license': 'LGPL-3',
    'depends': ['sale', 'account', 'it_contacts'],
    'data': [
        'report/proforma_invoice_report.xml',
        'report/tax_invoice_enhancements.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}
