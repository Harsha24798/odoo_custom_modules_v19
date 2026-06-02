from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime

# ╔═══════════════════════════════════════════════════════════════╗
# ║ QUOTATION APPROVAL LOGIC                                      ║
# ║                                                               ║
# ║ This model EXTENDS sale.order (quotations/sales orders)      ║
# ║ with approval workflow functionality.                         ║
# ╚═══════════════════════════════════════════════════════════════╝


class SaleOrder(models.Model):
    """Extend Sale Order with quotation approval workflow"""

    _inherit = 'sale.order'
    # ↑ Extend = add to existing sale.order model

    # ═════════════════════════════════════════════════════════════
    # FIELD 1: Approval Status (pending/approved/rejected)
    # ═════════════════════════════════════════════════════════════

    approval_status = fields.Selection(
        selection=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string="Approval Status",
        default='pending',  # Start as pending
        tracking=True  # Track changes in messenger
    )

    # ═════════════════════════════════════════════════════════════
    # FIELD 2: Do we need approval? (Computed - not stored)
    # ═════════════════════════════════════════════════════════════

    is_approval_required = fields.Boolean(
        string="Approval Required",
        compute='_compute_approval_required',
        # ↑ compute: Instead of storing, CALCULATE this value each time
        # ↑ Points to the method _compute_approval_required
        store=False  # ↑ Don't save to database
    )

    # ═════════════════════════════════════════════════════════════
    # FIELD 3: Who approved it?
    # ═════════════════════════════════════════════════════════════

    approved_by_user_id = fields.Many2one(
        'res.users',  # Links to user model
        string="Approved By",
        readonly=True  # Can't change in form, only programmatically
    )

    # ═════════════════════════════════════════════════════════════
    # FIELD 4: When was it approved?
    # ═════════════════════════════════════════════════════════════

    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True
    )

    # ═════════════════════════════════════════════════════════════
    # METHOD 1: Calculate if approval is needed
    # ═════════════════════════════════════════════════════════════

    @api.depends()
    def _compute_approval_required(self):
        """
        Decide: Does this quotation need approval?

        Logic:
        1. Is approval enabled in settings? YES/NO
        2. Is quotation amount > threshold? YES/NO
        3. If BOTH are YES → approval_required = TRUE

        This runs automatically when reading is_approval_required field
        """

        for order in self:
            # ─────────────────────────────────────────────────────
            # Step 1: Read setting - Is approval enabled?
            # ─────────────────────────────────────────────────────

            approval_enabled = self.env['ir.config_parameter'].sudo().get_param(
                'quotation_approval.enable_approval',
                # ↑ Key name (same as in res_config_settings.py)
                default='False'
            ) == 'True'
            # ↑ get_param returns string, compare with text 'True'

            # ─────────────────────────────────────────────────────
            # Step 2: Read setting - What's the threshold?
            # ─────────────────────────────────────────────────────

            threshold = float(
                self.env['ir.config_parameter'].sudo().get_param(
                    'quotation_approval.threshold_amount',
                    default='0'
                )
            )  # Convert to number for comparison

            # ─────────────────────────────────────────────────────
            # Step 3: Calculate - Is approval needed?
            # ─────────────────────────────────────────────────────

            order.is_approval_required = (
                approval_enabled and              # AND
                order.amount_total > threshold    # AND
            )
            # ↑ Both conditions must be True

    # ═════════════════════════════════════════════════════════════
    # METHOD 2: User clicks "Mark as Approved" button
    # ═════════════════════════════════════════════════════════════

    def action_set_approval_status(self):
        """Mark quotation as approved by current user"""

        for order in self:
            order.approval_status = 'approved'  # Change status
            order.approved_by_user_id = self.env.user.id  # Who did it
            order.approval_date = datetime.now()  # When did it

    # ═════════════════════════════════════════════════════════════
    # METHOD 3: User clicks "Reject" button
    # ═════════════════════════════════════════════════════════════

    def action_reject_approval(self):
        """Mark quotation as rejected"""

        for order in self:
            order.approval_status = 'rejected'  # Reject it

    # ═════════════════════════════════════════════════════════════
    # METHOD 4: Override confirmation - Check approval!
    # ═════════════════════════════════════════════════════════════

    def action_confirm(self):
        """
        OVERRIDE the standard confirmation method.

        Before allowing confirmation, check if approval is needed
        and if it's actually been approved.

        If approval needed but NOT done → Block with error
        If approved (or not needed) → Allow confirmation
        """

        for order in self:
            # Is approval required for this quotation?
            if order.is_approval_required:
                # Yes, approval is needed
                # But has it been approved?
                if order.approval_status != 'approved':
                    # NO! It hasn't been approved
                    # Block the confirmation
                    raise ValidationError(
                        f"Quotation {order.name} requires approval before confirmation!"
                    )
                    # ↑ This stops the process and shows error to user

        # If we reach here, either:
        # - Approval not needed, OR
        # - Approval needed AND already done

        # Call the original confirmation method
        return super().action_confirm()
        # ↑ super() = parent class (sale.order)
        # ↑ Run the original confirmation logic

# ═══════════════════════════════════════════════════════════════
#
# WORKFLOW EXAMPLE:
#
# 1. Manager creates 15,000 quotation
#    Settings: threshold=10,000, enabled=True
#
# 2. Odoo calls _compute_approval_required
#    - 15,000 > 10,000? YES
#    - Enabled? YES
#    - Result: is_approval_required = TRUE
#
# 3. Form shows approval buttons
#    (because is_approval_required = TRUE)
#
# 4. Approval Manager clicks "Mark as Approved"
#    - action_set_approval_status() runs
#    - approval_status = 'approved'
#    - approved_by_user_id = 'John'
#    - approval_date = '2026-05-08 10:30'
#
# 5. Manager clicks "Confirm Order"
#    - action_confirm() runs
#    - Checks: is_approval_required? YES
#    - Checks: is approved? YES
#    - Allows confirmation ✓
#
# 6. If confirmed WITHOUT approval:
#    - action_confirm() runs
#    - Checks: is_approval_required? YES
#    - Checks: is approved? NO
#    - Raises ValidationError ✗
#
# ═══════════════════════════════════════════════════════════════
