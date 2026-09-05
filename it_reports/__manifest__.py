{
    'name': 'Inova Technology - Report Layouts',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Custom report layouts for Inova Technology, starting with the Proforma Invoice',
    'author': 'Inova Technology',
    'website': 'https://inova.technology',
    'maintainer': 'Inova Technology',
    'license': 'LGPL-3',
    'depends': ['sale', 'it_contacts'],
    'data': [
        'report/proforma_invoice_report.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
