# Quick Implementation Guide - Real Estate Ads

**Goal**: Make your module production-ready in minimal time  
**Estimated Time**: 10-15 hours  
**Difficulty**: Beginner to Intermediate

---

## Step-by-Step Implementation

### STEP 1: Add Tests (2 hours)

#### 1.1 Create Test Directory

```bash
# Create folder structure
mkdir tests
touch tests/__init__.py
```

#### 1.2 Create Basic Test File

**File**: `tests/test_property.py`

```python
from odoo.tests import common
from odoo.exceptions import ValidationError

class TestPropertyModel(common.TransactionCase):
    """Test estate.property model."""
    
    def setUp(self):
        super().setUp()
        self.Property = self.env['estate.property']
    
    def test_property_creation_with_defaults(self):
        """Test creating property sets correct defaults."""
        prop = self.Property.create({
            'name': 'Test House',
            'expected_price': 500000,
        })
        # Verify defaults
        self.assertEqual(prop.state, 'new')
        self.assertEqual(prop.offer_count, 0)
        self.assertFalse(prop.garage)
        self.assertFalse(prop.garden)
    
    def test_total_area_calculation(self):
        """Test total area computation."""
        prop = self.Property.create({
            'name': 'House with Garden',
            'living_area': 100,
            'garden_area': 50,
        })
        self.assertEqual(prop.total_area, 150)
    
    def test_price_validation(self):
        """Test expected price cannot be negative."""
        with self.assertRaises(ValidationError):
            self.Property.create({
                'name': 'Invalid',
                'expected_price': -1000,
            })
    
    def test_offer_count_updates(self):
        """Test offer count reflects number of offers."""
        prop = self.Property.create({
            'name': 'Test',
            'expected_price': 500000,
        })
        self.assertEqual(prop.offer_count, 0)
        
        # Create offer
        self.env['estate.property.offers'].create({
            'property_id': prop.id,
            'price': 480000,
            'validity': 7,
            'partner_id': self.env.user.partner_id.id,
        })
        
        # Check count updated
        self.assertEqual(prop.offer_count, 1)
```

**File**: `tests/test_offers.py`

```python
from odoo.tests import common
from odoo.exceptions import ValidationError, AccessError

class TestOfferModel(common.TransactionCase):
    """Test estate.property.offers model."""
    
    def setUp(self):
        super().setUp()
        self.Offer = self.env['estate.property.offers']
        self.Property = self.env['estate.property']
        
        self.property = self.Property.create({
            'name': 'Test House',
            'expected_price': 500000,
        })
    
    def test_offer_price_validation(self):
        """Test offer price must be positive."""
        with self.assertRaises(ValidationError):
            self.Offer.create({
                'property_id': self.property.id,
                'price': 0,  # Invalid
                'validity': 7,
                'partner_id': self.env.user.partner_id.id,
            })
    
    def test_offer_creation(self):
        """Test valid offer creation."""
        offer = self.Offer.create({
            'property_id': self.property.id,
            'price': 480000,
            'validity': 7,
            'partner_id': self.env.user.partner_id.id,
        })
        
        self.assertEqual(offer.status, 'pending')
        self.assertEqual(offer.property_id, self.property)
    
    def test_accept_offer(self):
        """Test accepting offer workflow."""
        offer = self.Offer.create({
            'property_id': self.property.id,
            'price': 480000,
            'validity': 7,
            'partner_id': self.env.user.partner_id.id,
        })
        
        # Accept offer with manager
        manager_group = self.env.ref('real_estate_ads.group_property_manager')
        self.env.user.groups_id = [(4, manager_group.id)]
        
        offer.action_accept_offer()
        
        self.assertEqual(offer.status, 'accepted')
        self.assertEqual(self.property.state, 'accepted')
```

#### 1.3 Run Tests

```bash
# Run all tests
cd /path/to/odoo
python -m pytest /path/to/module/tests/ -v

# Run specific test file
python -m pytest /path/to/module/tests/test_property.py -v

# Run specific test class
python -m pytest /path/to/module/tests/test_property.py::TestPropertyModel -v
```

---

### STEP 2: Add Logging (1 hour)

#### 2.1 Import Logging

**Add to each model file** (property.py, property_offers.py):

```python
# At top of file, after other imports
import logging

logger = logging.getLogger(__name__)
```

#### 2.2 Add Logging Statements

**Example for property.py**:

```python
def action_sold(self):
    """Mark property as sold."""
    if not self.env.user.has_group('real_estate_ads.group_property_manager'):
        logger.warning(
            f"Non-manager user {self.env.user.name} attempted to mark "
            f"property {self.name} as sold"
        )
        raise AccessError('Only managers can mark properties as sold')
    
    logger.info(
        f"Property '{self.name}' (ID: {self.id}) marked as SOLD by "
        f"{self.env.user.name}"
    )
    self.write({'state': 'sold'})

def action_cancel(self):
    """Cancel property."""
    logger.info(
        f"Property '{self.name}' (ID: {self.id}) CANCELLED by "
        f"{self.env.user.name}"
    )
    self.write({'state': 'cancel'})
```

**Example for property_offers.py**:

```python
def action_accept_offer(self):
    """Accept offer."""
    # Check permission
    if not (self.env.user.has_group('real_estate_ads.group_property_sales') or
            self.env.user.has_group('real_estate_ads.group_property_manager')):
        logger.warning(
            f"User {self.env.user.name} without sales permission attempted "
            f"to accept offer {self.id}"
        )
        raise AccessError('You do not have the rights to accept offers.')
    
    logger.info(f"Offer {self.id}: ${self.price} for property "
                f"'{self.property_id.name}' ACCEPTED")
    
    # ... existing logic ...
    
    logger.info(
        f"Property '{self.property_id.name}' state changed to ACCEPTED"
    )
```

---

### STEP 3: Add Comprehensive Docstrings (2 hours)

#### 3.1 Update Method Docstrings

**Before**:
```python
def action_accept_offer(self):
    # Accept the offer
    self.write({'status': 'accepted'})
```

**After**:
```python
def action_accept_offer(self):
    """
    Accept the offer and update related property state.
    
    This method:
    - Validates user has sales/manager permissions
    - Prevents multiple accepted offers on same property
    - Marks this offer as accepted
    - Updates property state to 'accepted'
    - Automatically refuses competing offers
    
    Raises:
        AccessError: If user lacks sales/manager group
        ValidationError: If property already has accepted offer
    
    Example:
        >>> offer = env['estate.property.offers'].browse(123)
        >>> offer.action_accept_offer()
        >>> offer.status  # 'accepted'
    """
    # Validate permissions
    if not (self.env.user.has_group('real_estate_ads.group_property_sales') or
            self.env.user.has_group('real_estate_ads.group_property_manager')):
        raise AccessError(_('You do not have the rights to accept offers.'))
    
    # ... rest of implementation
```

#### 3.2 Update Computed Field Docstrings

```python
@api.depends('living_area', 'garden_area')
def _compute_total_area(self):
    """
    Compute total property area in square meters.
    
    Total area = living_area + garden_area
    
    Handles None values by treating as 0.
    """
    for record in self:
        record.total_area = (record.living_area or 0) + (record.garden_area or 0)

@api.depends('offer_ids.price')
def _compute_best_offer(self):
    """
    Compute the highest offer price received.
    
    Returns 0.0 if no offers exist.
    """
    for record in self:
        prices = record.offer_ids.mapped('price')
        record.best_offer = max(prices) if prices else 0.0
```

---

### STEP 4: Create README.md (30 minutes)

**File**: `README.md` in module root

```markdown
# Real Estate Ads Module

Complete property and offer management system for Odoo 19.

## Features

- **Property Management**: Create and manage real estate properties
- **Offer Tracking**: Receive and manage buyer offers
- **Automatic Calculations**: Best offer, total area, selling price
- **Role-Based Access**: Three security tiers
- **Workflow Automation**: Auto-refuse competing offers
- **Multi-View Support**: Form, List, Kanban, Pivot, Graph views

## Installation

1. Extract to Odoo addons directory
2. Install: Settings → Apps → Update Apps List → Install
3. Configure: Assign users to security groups

## Quick Start

1. Navigate: Real Estate Ads → Properties
2. Create Property: Click Create, fill in details
3. Receive Offers: Customers create offers
4. Accept Offer: Sales team accepts and manages

## Security Groups

- **Property User**: View properties, create own offers
- **Property Sales**: Accept/refuse offers, manage all
- **Property Manager**: Full administrative access

## Models

| Model | Purpose |
|-------|---------|
| `estate.property` | Property information |
| `estate.property.offers` | Buyer offers |
| `estate.property.type` | Property types |
| `estate.property.tags` | Property tags |

## Support

See documentation files for detailed guides.
```

---

### STEP 5: Add Input Validation (1.5 hours)

**File**: Add to `models/property.py`

```python
@api.constrains('living_area', 'garden_area', 'bedrooms', 'facades')
def _check_positive_values(self):
    """Validate all size/count fields are non-negative."""
    for record in self:
        if record.living_area is not None and record.living_area < 0:
            raise ValidationError(_('Living area cannot be negative'))
        if record.garden_area is not None and record.garden_area < 0:
            raise ValidationError(_('Garden area cannot be negative'))
        if record.bedrooms is not None and record.bedrooms < 0:
            raise ValidationError(_('Number of bedrooms cannot be negative'))
        if record.facades is not None and record.facades < 0:
            raise ValidationError(_('Number of facades cannot be negative'))

@api.constrains('date_availability')
def _check_availability_not_past(self):
    """Validate availability date is not in past."""
    from datetime import date
    for record in self:
        if record.date_availability and record.date_availability < date.today():
            raise ValidationError(
                _('Availability date cannot be in the past')
            )
```

**File**: Add to `models/property_offers.py`

```python
@api.constrains('validity')
def _check_validity_positive(self):
    """Validate validity is positive number of days."""
    for record in self:
        if record.validity and record.validity <= 0:
            raise ValidationError(
                _('Offer validity must be greater than 0 days')
            )
```

---

### STEP 6: Review and Enhance Security Views (1.5 hours)

**Verify in your view files** (`views/property_view.xml`):

```xml
<!-- ✅ SHOULD HAVE: readonly for non-managers -->
<field name="name" readonly="not is_manager"/>

<!-- ✅ SHOULD HAVE: invisible for non-managers -->
<field name="type_id" invisible="not is_manager"/>

<!-- ✅ SHOULD HAVE: buttons shown only to sales -->
<button name="action_accept_offer"
    string="Accept"
    type="object"
    groups="real_estate_ads.group_property_sales"
    invisible="status != 'pending'"/>
```

**If missing, add the is_manager field to your form**:

```xml
<!-- Add this to make is_manager available -->
<field name="is_manager" invisible="1"/>
```

---

## Verification: Before/After

### Current Status (Before)

```
Code Quality:       7/10 ❌
Authentication:     1/10 ❌ CRITICAL
Documentation:      6/10 ❌
Logging:            2/10 ❌ CRITICAL
Error Messages:     7/10 ✅
────────────────────────────────
Overall Score:      4.6/10 ❌ NOT PRODUCTION READY
```

### Target Status (After)

```
Code Quality:       8/10 ✅
Authentication:     9/10 ✅
Documentation:      9/10 ✅
Logging:            8/10 ✅
Error Messages:     9/10 ✅
────────────────────────────────
Overall Score:      8.6/10 ✅ PRODUCTION READY
```

---

## Quick Time Estimate

| Task | Time | Status |
|------|------|--------|
| Add Tests | 2 hrs | ⏳ |
| Add Logging | 1 hr | ⏳ |
| Add Docstrings | 2 hrs | ⏳ |
| Create README | 0.5 hrs | ⏳ |
| Add Validation | 1.5 hrs | ⏳ |
| Review Security | 1.5 hrs | ⏳ |
| **TOTAL** | **8.5 hrs** | ⏳ |

---

## Critical Paths to Test Manually

After implementing above, test these workflows:

### Test 1: Property Creation
1. Navigate: Real Estate Ads → Properties → Create
2. Fill: Name, Type, Price, Area
3. Save
4. Verify: State is 'new', offer_count is 0

### Test 2: Offer Creation & Acceptance
1. Open a property
2. Add offer with price < expected_price
3. As sales user, click "Accept" button
4. Verify: Offer status = 'accepted', property state = 'accepted'

### Test 3: Permission Check
1. Log in as Property User (not sales)
2. Try to accept offer
3. Verify: Button hidden, AccessError if trying via API

### Test 4: Validation Check
1. Try to create property with negative area
2. Verify: ValidationError message appears

### Test 5: Deadline Extension (Cron Job) - **NEW**
1. Create offer with validity = 7 days (deadline = today + 7)
2. Wait or manually set deadline to past date
3. Run cron job: `_cron_extend_offer_deadline()`
4. Verify:
   - ✅ deadline extended to today + 7
   - ✅ validity recalculated correctly (32 days in example)
   - ✅ Refresh page → validity STILL shows 32 (not reverted to 7)
   - ✅ Restart server → validity STILL shows 32 ✅

**This is critical for data persistence!**

---

## File Changes Summary

### Files to Create
- ✅ `tests/__init__.py` (empty)
- ✅ `tests/test_property.py`
- ✅ `tests/test_offers.py`
- ✅ `README.md`

### Files to Modify
- ✅ `models/property.py` (add logging + validation)
- ✅ `models/property_offers.py` (add logging + validation)
- ✅ `views/property_view.xml` (verify is_manager field)

### Files to Review
- ✅ `__manifest__.py` (already good)
- ✅ `security/` files (already good)

---

## Next: Deploy to Production

After completing above:

1. ✅ Run all tests: `pytest tests/`
2. ✅ Code quality check: `pylint models/`
3. ✅ Manual testing: Follow test scenarios above
4. ✅ Security audit: Review access control
5. ✅ Performance test: Try with 1000+ records
6. ✅ Deploy: Follow deployment procedure

---

## Success Criteria

You're ready when:

- [x] All 8.5 hours of tasks complete
- [x] All tests passing
- [x] Manual test scenarios working
- [x] No errors in production logs
- [x] Security verified
- [x] Team reviewed code
- [x] Stakeholders approved

---

**Time to Complete**: 8-10 hours  
**Difficulty**: Beginner  
**Result**: Production-ready module ✅

---

**Version**: 1.0  
**Date**: May 21, 2026  
**Odoo**: 19.0

