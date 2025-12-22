{
    'name': 'KST Base',
    'version': '1.1.0',
    'category': 'KST/Base',
    'summary': 'Shared masterfiles for KST modules (Banks, KCode, Utility Accounts)',
    'description': """
KST Base Module
================
This module provides shared masterfiles used across all KST modules:
* Banks - Bank accounts for deposits and transactions
* KCode - General purpose codes for identification
* Utility Accounts - Utility provider accounts (MERALCO, Water)
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
    ],
    'demo': [
        'demo/kst_base_demo.xml',
    ],
}

