{
    'name': 'Vouchers',
    'version': '1.0.0',
    'category': 'Vouchers',
    'summary': 'Manage expenses, suppliers, and check voucher disbursements',
    'description': """
Vouchers Module
===============
This module manages:
* Expense categories and masterlist
* Payees/Suppliers information
* Voucher prefixes for identification
* Check voucher processing and tracking
* Voucher detail line items
    """,
    'depends': [
        'base',
        'mail',
        'general',
    ],
    'application': True,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/expense_category_views.xml',
        'views/expense_views.xml',
        'views/payee_views.xml',
        'views/voucher_prefix_views.xml',
        'views/voucher_header_views.xml',
        'views/voucher_detail_views.xml',
    ],
    'demo': [
        'demo/vouchers_demo.xml',
    ],
}



