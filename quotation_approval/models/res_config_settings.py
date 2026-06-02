from odoo import models, fields

# ╔═══════════════════════════════════════════════════════════════╗
# ║ SETTINGS MODEL - WHAT IS THIS?                               ║
# ║                                                               ║
# ║ res.config.settings is Odoo's model for system settings      ║
# ║ We inherit it to add our custom approval settings            ║
# ║                                                               ║
# ║ When user goes to:                                           ║
# ║ Sales → Configuration → Settings                            ║
# ║ They see and modify fields defined here.                    ║
# ╚═══════════════════════════════════════════════════════════════╝


class ResConfigSettings(models.TransientModel):
    """
    Transient model for storing quotation approval settings.

    TransientModel vs Model:
    - Model: Permanent data stored in database
    - TransientModel: Temporary data, auto-deleted

    Settings are transient because they're loaded/saved temporarily
    """

    _inherit = 'res.config.settings'
    # ↑ _inherit: We extend the existing res.config.settings model
    # ↑ This means: take all its fields + add ours

    # ═════════════════════════════════════════════════════════════
    # SETTING 1: ENABLE/DISABLE APPROVAL
    # ═════════════════════════════════════════════════════════════

    quotation_approval_enabled = fields.Boolean(
        string="Enable Quotation Approval",
        # ↑ The label user sees in the form

        help="Check this to require approval before confirming quotations.",
        # ↑ Tooltip shown on hover

        config_parameter='quotation_approval.enable_approval',
        # ↑ KEY LINE: This is where the setting is STORED
        # ↑ Not stored in sale_order table
        # ↑ Stored in ir.config_parameter (system-wide settings)
        # ↑ Name format: {module_name}.{setting_name}

        default=False
        # ↑ Default: Unchecked (disabled)
    )

    # ═════════════════════════════════════════════════════════════
    # SETTING 2: APPROVAL THRESHOLD AMOUNT
    # ═════════════════════════════════════════════════════════════

    quotation_approval_threshold = fields.Float(
        string="Approval Threshold Amount",
        # ↑ Label in form

        help="Quotations above this amount require approval. Set 0 for all quotations.",
        # ↑ Help text

        config_parameter='quotation_approval.threshold_amount',
        # ↑ WHERE it's stored in database

        default=0.0
        # ↑ Default threshold: 10,000
        # ↑ Means: amounts > 10,000 need approval
    )

# ═══════════════════════════════════════════════════════════════
# HOW THIS WORKS - THE FLOW:
# ═══════════════════════════════════════════════════════════════
#
# 1. User navigates to: Sales → Configuration → Settings
#
# 2. Odoo finds our module and loads ResConfigSettings
#
# 3. Shows form with:
#    - Checkbox: "Enable Quotation Approval"
#    - Number field: "Approval Threshold Amount"
#
# 4. User checks the box and sets threshold to 5000
#
# 5. User clicks "Save"
#
# 6. Odoo saves to ir.config_parameter table:
#    Key: 'quotation_approval.enable_approval' → Value: True
#    Key: 'quotation_approval.threshold_amount' → Value: 5000.0
#
# 7. Later, when user creates a 8000 quotation:
#    - Our quotation logic reads these settings
#    - Sees: enabled=True, threshold=5000
#    - 8000 > 5000 → Approval required!
#
# ═══════════════════════════════════════════════════════════════
