{
    'name': 'Units',
    'version': '1.0.1',
    'category': 'Units',
    'summary': 'Manage unit rentals, lease contracts, and rent collections',
    'description': """
Units Module
============
This module manages:
* Locations and unit categories
* Units being leased
* Lessees (tenants) and Lessors (property owners)
* Rental contracts with escalation terms
* Unit rent collections and payment tracking
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
        'views/location_views.xml',
        'views/unit_category_views.xml',
        'views/lessor_views.xml',
        'views/lessee_views.xml',
        'views/unit_views.xml',
        'views/contract_views.xml',
        'views/unit_rent_transaction_views.xml',
        'views/unit_utility_transaction_views.xml',
        'views/unit_utility_bill_views.xml',
        'views/utility_account_views.xml',
        'views/payment_attachment_views.xml',
    ],
    'demo': [
        'demo/units_demo.xml',
        'demo/masterfiles_demo.xml',
    ],
}

