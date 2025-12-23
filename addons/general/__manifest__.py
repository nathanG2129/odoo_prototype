{
    'name': 'General',
    'version': '1.1.0',
    'category': 'General',
    'summary': 'Shared masterfiles for modules (Banks, KCode, Utility Accounts)',
    'description': """
General Module
==============
This module provides shared masterfiles used across all modules:
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
        'demo/general_demo.xml',
    ],
}

