{
    'name': 'Real Estate Management',
    'version': '1.0',
    'category': 'Real Estate/Brokerage',
    'depends': [
        'base',
    ],
    'application': True,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/estate.property.type.csv',
        'views/estate_property_offer_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_property_views.xml',
        'views/res_users_views.xml',
        'demo/estate_property_demo.xml',
    ],
}