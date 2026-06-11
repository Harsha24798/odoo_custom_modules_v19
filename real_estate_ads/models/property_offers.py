from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import ValidationError, AccessError


class PropertyOffers(models.Model):
    _name = 'estate.property.offers'
    _description = 'Property Offers'
    _order = 'creation_date DESC'

    # Regular Fields
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True,
        index=True,
    )

    name = fields.Char(string='Name', compute='_compute_name')

    # Use Monetary for offer price and inherit property's currency via related field
    currency_id = fields.Many2one('res.currency', string='Currency', related='property_id.currency_id', store=False, readonly=True)

    price = fields.Monetary(
        string='Price',
        currency_field='currency_id',
        required=True,
        help='Offer price for the property'
    )
    status = fields.Selection(
        [('accepted', 'Accepted'), ('refused', 'Refused'), ('pending', 'Pending')],
        string='Status',
        default='pending',
        index=True,
        help='Status of the offer'
    )
    validity = fields.Integer(
        string='Validity (Days)',
        compute='_compute_validity',
        store=True,
        # required=True,
        help='Number of days the offer is valid (auto-calculated from deadline - creation_date)'
    )

    # Autopopulated date field
    creation_date = fields.Date(
        string='Created Date',
        default=fields.Date.today,
        required=True,
        help='Date when the offer was created'
    )

    # Many-to-One Relations
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        index=True,
        help='Customer making the offer'
    )
    property_id = fields.Many2one(
        'estate.property',
        string='Property',
        required=True,
        index=True,
        help='Property for which the offer is made'
    )

    # Convenience related field to expose the property's state on the offer
    # This avoids using dotted expressions like `property_id.state` in view attrs
    # which can cause parsing issues in the web client. Use this field in
    # view attrs/domains instead of a dotted path.
    property_state = fields.Selection(related='property_id.state', string='Property State', readonly=True, store=False)

    # Regular stored field (set on creation, can be extended by cron or manual edit)
    deadline = fields.Date(
        string='Deadline',
        index=True,
        help='Expiry date of the offer (auto-calculated at creation, editable or extended by cron)',
        readonly=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-link offers to the current user's partner if not provided.
        Advances property state to 'received' when the first offer arrives.
        Calculate and set deadline based on creation_date and a default 7-day validity.
        """
        for vals in vals_list:
            if not vals.get('partner_id') and self.env.user.partner_id:
                vals['partner_id'] = self.env.user.partner_id.id

            # Set deadline on creation if not already provided
            if 'deadline' not in vals and ('validity' in vals or 'creation_date' in vals):
                creation_date = vals.get('creation_date', fields.Date.today())
                validity = vals.get('validity', 7)
                days = max(validity or 1, 1)
                vals['deadline'] = fields.Date.to_date(creation_date) + timedelta(days=days)

            # If no deadline is set at all, use creation_date + 7 days
            if 'deadline' not in vals:
                creation_date = vals.get('creation_date', fields.Date.today())
                vals['deadline'] = fields.Date.to_date(creation_date) + timedelta(days=7)

        records = super().create(vals_list)
        for record in records:
            if record.property_id and record.property_id.state == 'new':
                record.property_id.state = 'received'
        return records

    # def _compute_deadline(self):
    #     """(DEPRECATED) Kept for backward compatibility. Deadline is now a regular field."""
    #     pass

    @api.depends('deadline', 'creation_date')
    def _compute_validity(self):
        """Compute validity as the difference between deadline and creation_date.

        This ensures validity is always correct:
        validity = deadline - creation_date (in days), minimum 1 day
        """
        for record in self:
            if record.deadline and record.creation_date:
                cd = fields.Date.to_date(record.creation_date)
                dl = fields.Date.to_date(record.deadline)
                record.validity = max((dl - cd).days, 1)
            else:
                # Fallback to 1 day if either date is missing
                record.validity = 1

    def write(self, vals):
        """Override write - no need to recalculate validity anymore.

        Validity is now a computed stored field that automatically updates
        when deadline or creation_date change.
        """
        return super().write(vals)

    def _compute_validity_from_deadline(self, base_date, deadline):
        """Return validity days derived from base_date -> deadline with a minimum of 1 day."""
        if not deadline:
            return 1
        base = fields.Date.to_date(base_date) if base_date else fields.Date.today()
        dl = fields.Date.to_date(deadline)
        return max((dl - base).days, 1)

    @api.onchange('creation_date', 'validity')
    def _onchange_validity(self):
        """When user changes validity on the form, update deadline accordingly.

        This provides UI responsiveness during form editing.
        Formula: deadline = creation_date + validity
        """
        for record in self:
            if record.creation_date and record.validity:
                days = max(record.validity or 1, 1)
                record.deadline = record.creation_date + timedelta(days=days)

    # def _inverse_deadline(self):
    #     """(DEPRECATED) No longer needed. Deadline is now a regular field."""
    #     pass

    @api.constrains('price')
    def _check_price_positive(self):
        """Validate that price is positive."""
        for record in self:
            if record.price <= 0:
                raise ValidationError('Offer price must be greater than 0.')

    @api.constrains('validity')
    def _check_validity_positive(self):
        """Validate that validity is positive."""
        for record in self:
            if record.validity <= 0:
                raise ValidationError('Validity must be greater than 0 days.')

    @api.depends('partner_id', 'property_id')
    def _compute_name(self):
        """Compute the name of the offer based on the customer and property."""
        for record in self:
            partner_name = record.partner_id.name if record.partner_id else 'Unknown Customer'
            property_name = record.property_id.name if record.property_id else 'Unknown Property'
            record.name = f'{partner_name} - {property_name}'

    def action_accept_offer(self):
        """Accept the offer, update the property state, and refuse other offers."""
        if not (self.env.user.has_group('real_estate_ads.group_property_sales') or self.env.user.has_group('real_estate_ads.group_property_manager')):
            raise AccessError('You do not have the rights to accept offers.')

        # Guard: block if another accepted offer already exists for any of these properties.
        for offer in self:
            if offer.property_id:
                already_accepted = self.env['estate.property.offers'].search([
                    ('property_id', '=', offer.property_id.id),
                    ('status', '=', 'accepted'),
                    ('id', '!=', offer.id),
                ], limit=1)
                if already_accepted:
                    raise ValidationError(
                        'This property already has an accepted offer (ID: %s). '
                        'Refuse the existing accepted offer before accepting another.' % already_accepted.id
                    )

        self.write({'status': 'accepted'})
        unique_properties = self.mapped('property_id')
        unique_properties.write({'state': 'accepted'})
        # Refuse all other non-refused offers for the same properties in one query.
        self.env['estate.property.offers'].search([
            ('property_id', 'in', unique_properties.ids),
            ('id', 'not in', self.ids),
            ('status', '!=', 'refused'),
        ]).write({'status': 'refused'})

    def action_refuse_offer(self):
        """Refuse the offer. Reverts property state to 'new' if no pending/accepted offers remain."""
        if not (self.env.user.has_group('real_estate_ads.group_property_sales') or self.env.user.has_group('real_estate_ads.group_property_manager')):
            raise AccessError('You do not have the rights to refuse offers.')

        self.write({'status': 'refused'})
        # One state update per unique property, not per offer.
        for prop in self.mapped('property_id'):
            has_active = self.env['estate.property.offers'].search([
                ('property_id', '=', prop.id),
                ('status', 'in', ['pending', 'accepted']),
            ], limit=1)
            prop.state = 'received' if has_active else 'new'

