{
    'name': 'Markets',
    'version': '2.0.0',
    'category': 'Markets',
    'summary': 'Manage market rentals, stall listings, utility bills, and rent/utility collections',
    'description': """
        Markets Module
        ==============
        This module manages:
        * Markets and stall masterfiles
        * Tenant information
        * Utility accounts and provider bills (MERALCO, Water)
        * Market rent collections
        * Utility (electricity and water) billing and collections
        * Derived rates and metered vs. flat-rate billing
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
        'views/market_views.xml',
        'views/tenant_views.xml',
        'views/market_pay_type_views.xml',
        'views/stall_views.xml',
        'views/payment_attachment_views.xml',
        'views/market_rent_transaction_views.xml',
        'views/market_rent_batch_views.xml',
        'views/market_utility_transaction_views.xml',
        'views/utility_bill_views.xml',
        'views/utility_account_views.xml',
    ],
    'demo': [
        'demo/markets_demo.xml',      # Markets (must be first)
        'demo/pay_types.xml',          # Pay Types (needed before stalls)
        'demo/standardized_stalls.xml', # Stalls (depends on markets and pay types)
    ],
}

