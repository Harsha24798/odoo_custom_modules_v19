{
    # Basic Module Information
    'name': 'Quotation Approval',
    # ↑ This is the name users see in Apps store

    'version': '19.0.1.0.0',
    # ↑ Format: {OdooVersion}.{Major}.{Minor}.{Patch}.{Fix}
    # ↑ We use 19.0 because we're building for Odoo 19

    'summary': 'Add approval workflow for sales quotations',
    # ↑ Short description shown in Apps list

    'description': '''
        Quotation Approval Module
        =========================
        
        This module adds an approval workflow to sales quotations, similar to 
        purchase RFQ approval. Features:
        
        * Enable/disable approval requirement in settings
        * Set approval threshold by amount
        * Approval required before confirming quotations
        * Track who approved and when
    ''',
    # ↑ Detailed description shown when user clicks the module

    'author': 'Harsha Madushan',
    # ↑ Author name

    'license': 'LGPL-3',
    # ↑ License type (LGPL-3 is standard for Odoo)

    'category': 'Sales',
    # ↑ Category in Odoo Apps (Sales, Accounting, Inventory, etc.)

    'depends': ['sale'],
    # ↑ IMPORTANT: List modules this one depends on
    # ↑ 'sale' = our module needs the Sales app installed first
    # ↑ If Sales app isn't installed, Odoo won't let us install this

    'data': [
        # ↑ List of XML/CSV files to load
        # ↑ Order matters! Load views after models
        'views/res_config_settings_views.xml',
        # ↑ Settings form view
        'views/sale_order_views.xml',
        # ↑ Quotation form view
    ],
    # ↑ These files must exist or Odoo will error on install

    'installable': True,
    # ↑ Can this module be installed? (True/False)

    'application': True,
    # ↑ IMPORTANT: Set to True to make it visible in Apps list
    # ↑ True = Standalone app (shows in main Apps)
    # ↑ False = Add-on only (shows in Modules list only)

    'auto_install': False,
    # ↑ Auto-install when dependencies are installed?
    # ↑ False = user must manually click Install

    'sequence': 1,
    # ↑ Order in which module appears in Apps list
    # ↑ Lower number = appears earlier in the list
    # ↑ Useful for organizing modules
}
# ↑ This dictionary is what tells Odoo everything about your module

