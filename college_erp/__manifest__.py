{
    'name': 'College Erp',
    'version': '19.0.1.0.0',
    'author': 'Harsha Madushan',
    'category': 'Education',
    'website': 'https://www.harshamadusha.com',
    'summary': 'College ERP System',
    'description': """
        A comprehensive ERP system for managing college operations.
        
        01. Mange Students\n
        02. Manage Teachers\n
        03. Manage Courses\n
        04. Role Base System\n
        """,
    'license': 'LGPL-3',
    'sequence': 2,

    'depends': ['base', 'sale'],
    'data': [
        'security/college_erp_security.xml',
        'security/ir.model.access.csv',

        'data/ir_sequence_data.xml',

        'views/college_student_views.xml',
        'views/student_email_wizard_views.xml',
        'views/college_erp_menus_views.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
}