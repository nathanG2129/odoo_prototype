{
    'name': 'KST Units',
    'version': '1.0.1',
    'category': 'KST/Units',
    'summary': 'Manage unit rentals, lease contracts, and rent collections',
    'description': """
KST Units Module
==================
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
        'kst_base',
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
    ],
    'demo': [
        'demo/kst_units_demo.xml',
    ],
}

