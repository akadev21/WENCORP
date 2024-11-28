{
    'name': "Majesty",
    'sequence': -1,
    'summary': "A short summary of the module's purpose",
    'description': """
        A detailed description of the module's functionality.
        Describe what it does and any unique features it has.
    """,
    'author': "Your Name or Company",
    'website': "http://www.example.com",

    # Categories can be used to filter modules in modules listing
    'category': 'Category Name (e.g., Sales, Accounting)',
    'version': '1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'project', 'sale_management', 'product'  # Base Odoo module; adjust according to your module’s dependencies
    ],

    # always loaded
    'data': [
        # List XML files like views, security access rules, etc.
        'security/ir.model.access.csv',
        'views/menu_action.xml',
        'views/commercial_project_view.xml',
        'data/email_templates_designer.xml',
        'views/designer_project_view.xml',
        'views/commercial_sale_order.xml',
        'views/usine_view.xml',
        'views/prodect_template_view.xml',
        'views/customer_view.xml',
        'wizard/bta_cancel_wizard.xml',
        'wizard/client_command_wizard.xml',
    ],

    # Technical information
    'installable': True,
    'application': True,
    'auto_install': False,

    # Odoo 17 may support the license field, make sure to include the appropriate one
    'license': 'LGPL-3',
}
