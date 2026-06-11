from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError, UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class Property(models.Model):
    _name = 'estate.property'
    _inherit = ['mail.thread']
    _description = 'Real Estate Property'

    name = fields.Char(string='Name', required=True, index=True)
    description = fields.Text(string='Description')
    postcode = fields.Char(string='Postcode', index=True)
    date_availability = fields.Date(string='Available From', index=True)
    expected_price = fields.Monetary(string='Expected Price', currency_field='currency_id', tracking=True, index=True)
    bedrooms = fields.Integer(string='Bedrooms')
    living_area = fields.Integer(string='Living Area(sqm)')
    facades = fields.Integer(string='Facades')
    garage = fields.Boolean(string='Garage', default=False)
    garden = fields.Boolean(string='Garden', default=False)
    garden_area = fields.Integer(string='Garden Area')
    phone = fields.Char(string='Phone', related='buyer_id.phone', readonly=True)
    offer_count = fields.Integer(string="Offer Count", compute='_compute_offer_count', store=True)
    total_area = fields.Integer(string='Total Area', compute='_compute_total_area', store=True, help='Total area in sqm (living_area + garden_area)')

    state = fields.Selection([('new', 'New'), ('received', 'Offer Received'), ('accepted', 'Offer Accepted'), ('sold', 'Sold'), ('cancel', 'Canceled')], string='Status', default='new', index=True)
    garden_orientation = fields.Selection([('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')], string='Garden Orientation', default='north')

    best_offer = fields.Monetary(
        string='Best Offer',
        compute='_compute_best_offer',
        store=True,
        currency_field='currency_id',
        help='Highest offer price received for the property'
    )
    selling_price = fields.Monetary(
        string='Selling Price',
        compute='_compute_selling_price',
        store=True,
        currency_field='currency_id',
        help='Current sale price based on the accepted offer, or the highest offer if no offer is accepted yet'
    )

    # Many to Many
    tag_ids = fields.Many2many('estate.property.tags', string='Property Tags')

    # Many to One
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    type_id = fields.Many2one('estate.property.type', string='Property Type', index=True)
    sales_id = fields.Many2one('res.users', string='Salesman')
    buyer_id = fields.Many2one('res.partner', string='Buyer')

    # One to Many
    offer_ids = fields.One2many('estate.property.offers', 'property_id', string='Offers')

    # Computed field for UI access control (checks if current user is a manager)
    is_manager = fields.Boolean(
        string='Is Manager',
        compute='_compute_is_manager',
        help='Technical field: True if current user is in property manager group'
    )

    @api.depends_context('uid')
    def _compute_is_manager(self):
        """Check if the current user is a property manager."""
        for record in self:
            record.is_manager = self.env.user.has_group('real_estate_ads.group_property_manager')

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        """Compute total area as the sum of living area and garden area.

        Stored for easy searching/sorting in list views.
        """
        for record in self:
            record.total_area = (record.living_area or 0) + (record.garden_area or 0)

    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        """Compute the best offer as the highest related offer price."""
        for record in self:
            offer_prices = record.offer_ids.mapped('price')
            record.best_offer = max(offer_prices) if offer_prices else 0.0

    @api.onchange('offer_ids')
    def _onchange_offer_ids(self):
        """Keep best_offer and selling_price responsive in the form before save."""
        self._compute_best_offer()
        self._compute_selling_price()

    @api.depends('offer_ids.price', 'offer_ids.status')
    def _compute_selling_price(self):
        """Compute the selling price from the accepted offer, or fall back to the highest offer."""
        for record in self:
            accepted_offers = record.offer_ids.filtered(lambda offer: offer.status == 'accepted')
            if accepted_offers:
                record.selling_price = max(accepted_offers.mapped('price'))
            else:
                offer_prices = record.offer_ids.mapped('price')
                record.selling_price = max(offer_prices) if offer_prices else 0.0

    @api.constrains('expected_price')
    def _check_expected_price_non_negative(self):
        """Block negative expected price values at the application level."""
        for record in self:
            if record.expected_price is not None and record.expected_price < 0:
                raise ValidationError('Expected price must be non-negative.')

    def action_sold(self):
        if not self.env.user.has_group('real_estate_ads.group_property_sales'):
            raise AccessError('Only Property Sales or Managers can mark a property as sold.')
        self.state = 'sold'

    def action_cancel(self):
        if not self.env.user.has_group('real_estate_ads.group_property_sales'):
            raise AccessError('Only Property Sales or Managers can cancel a property.')
        self.state = 'cancel'

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        """Compute the number of offers for each property."""
        for record in self:
            record.offer_count = len(record.offer_ids)

    def action_property_view_offers(self):
        """Open the offers related to this property in a new window."""
        return {
            'name': f'{self.name} - Offers',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.property.offers',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
        }

    def _cron_extend_offer_deadline(self):
        """Cron: batch-extend expired pending offer deadlines by 7 days."""
        today = fields.Date.today()
        offers = self.env['estate.property.offers'].search([
            ('status', '=', 'pending'),
            ('deadline', '<', today),
        ])
        if not offers:
            return
        new_deadline = today + timedelta(days=7)
        offers.write({'deadline': new_deadline})
        _logger.info("Extended %d expired pending offer(s) to %s", len(offers), new_deadline)


    # Report
    def _get_report_base_filename(self):
        """Override the default report filename to include the property name."""
        self.ensure_one()
        return f"Estate Property - {self.name} Report"

    def action_send_email(self):
        self.ensure_one()
        template = self.env.ref('real_estate_ads.email_template_property', raise_if_not_found=False)
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': {
                'default_model': 'estate.property',
                'default_res_ids': self.ids,
                'default_use_template': bool(template),
                'default_template_id': template.id if template else False,
                'default_composition_mode': 'comment',
                'force_email': True,
            },
        }