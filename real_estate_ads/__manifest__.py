{
    'name': 'Real estate ads',
    'version': '19.0.1.0.0',
    'author': 'Harsha Madushan',
    'website': 'http://www.realestateads.com',
    'description': """
        Real estate ads models show available properties
        
        ° Add new Properties \n
        ° Search Properties \n
        ° Manage Properties \n
        ° View Properties details \n
        ° Delete Properties \n
        ° Update Properties \n
        ° Manage Property Types \n
        """,
    'category': 'Administration',
    'summary': 'Real estate ads',
    'license': 'LGPL-3',
    'sequence': 1,

    'depends': ['base', 'mail'],
    'data': [
        # Security Files
        'security/real_estate_ads_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule_offer.xml',

        # View Files
        'views/property_view.xml',
        'views/property_type_view.xml',
        'views/property_tag_view.xml',
        'views/property_offer_view.xml',
        'views/menu_items.xml',

        # Data Files
        'data/property_type.xml',
        'data/ir_cron.xml',

        # Report
        'report/report_estate_property.xml',
        'report/property_report.xml',
    ],
    'demo': [
        'demo/property_tag.xml',
        'demo/property.xml',
        'demo/property_offer.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}