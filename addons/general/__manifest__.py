{
    'name': 'General',
    'version': '1.2.0',
    'category': 'General',
    'summary': 'Shared masterfiles for modules (Banks, KCode, Utility Accounts, Payment Attachments)',
    'description': """
General Module
==============
This module provides shared masterfiles used across all modules:
* Banks - Bank accounts for deposits and transactions
* KCode - General purpose codes for identification
* Utility Accounts - Utility provider accounts (MERALCO, Water)
* Payment Attachments - Reusable attachment model for receipts (bank slips, GCash, Maya, etc.)
    """,
    'depends': [
        'base',
        'mail',
    ],
    'application': False,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/bank_views.xml',
        'views/kcode_views.xml',
        'views/utility_account_views.xml',
        'views/payment_attachment_views.xml',
    ],
    'demo': [
        'demo/general_demo.xml',
    ],
}

