# tests/__init__.py
# Empty file

# tests/test_property.py
from odoo.tests import common
from odoo.exceptions import ValidationError


class TestPropertyModel(common.TransactionCase):
    """Test estate.property model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Property = cls.env['estate.property']

    def test_property_creation(self):
        """Test basic property creation."""
        prop = self.Property.create({
            'name': 'Test House',
            'expected_price': 500000,
            'bedrooms': 3,
            'living_area': 150,
        })
        self.assertEqual(prop.state, 'new')
        self.assertEqual(prop.offer_count, 0)

    def test_total_area_computation(self):
        """Test total area computation."""
        prop = self.Property.create({
            'name': 'House with Garden',
            'living_area': 100,
            'garden_area': 200,
        })
        self.assertEqual(prop.total_area, 300)

    def test_expected_price_validation(self):
        """Test expected price must be non-negative."""
        with self.assertRaises(ValidationError):
            self.Property.create({
                'name': 'Invalid Property',
                'expected_price': -1000,
            })


# tests/test_offers.py
class TestOfferWorkflow(common.TransactionCase):
    """Test offer creation and acceptance."""

    def setUp(self):
        super().setUp()
        # In Odoo 19, has_group() always checks real DB membership (sudo() does NOT bypass it).
        # Add the test user to the sales group so accept/refuse actions work.
        # Note: Odoo 19 renamed res.groups.users → user_ids and res.users.groups_id → group_ids.
        self.env.ref('real_estate_ads.group_property_sales').write({'user_ids': [(4, self.env.uid)]})
        self.property = self.env['estate.property'].create({
            'name': 'Test House',
            'expected_price': 500000,
        })

    def test_offer_acceptance(self):
        """Test accepting offer workflow."""
        offer = self.env['estate.property.offers'].create({
            'property_id': self.property.id,
            'price': 480000,
            'validity': 7,
            'partner_id': self.env.user.partner_id.id,
        })

        # Creating an offer advances property state to 'received'
        self.assertEqual(offer.status, 'pending')
        self.assertEqual(self.property.state, 'received')

        offer.action_accept_offer()

        # After acceptance
        self.assertEqual(offer.status, 'accepted')
        self.assertEqual(self.property.state, 'accepted')


# tests/test_security.py
class TestSecurity(common.TransactionCase):
    """Test security rules and access control."""

    def test_user_cannot_access_manager_features(self):
        """Test non-sales user cannot mark properties as sold."""
        from odoo.exceptions import AccessError

        prop = self.env['estate.property'].create({
            'name': 'Test',
            'expected_price': 500000,
        })

        # public_user has no real estate groups — avoids creating a new partner
        # (other installed modules add NOT NULL columns that break partner creation).
        # Odoo's assertRaises does not accept a tuple; pass AccessError directly.
        user = self.env.ref('base.public_user')

        with self.assertRaises(AccessError):
            prop.with_user(user).action_sold()