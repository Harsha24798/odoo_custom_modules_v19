# Odoo 19 Best Practices & Production-Ready Coding Guide

> **For**: real_estate_ads module  
> **Odoo Version**: 19.0  
> **Date**: May 21, 2026  
> **Purpose**: Production-ready code standards and best practices

---

## Table of Contents

1. [Code Quality Standards](#code-quality-standards)
2. [File Organization](#file-organization)
3. [Model Best Practices](#model-best-practices)
4. [Field Definition Standards](#field-definition-standards)
5. [Business Logic](#business-logic)
6. [Security Best Practices](#security-best-practices)
7. [View and UI Standards](#view-and-ui-standards)
8. [Database and Performance](#database-and-performance)
9. [Testing Standards](#testing-standards)
10. [Error Handling](#error-handling)
11. [Documentation Standards](#documentation-standards)
12. [Code Review Checklist](#code-review-checklist)

---

## Code Quality Standards

### 1. Python Code Style (PEP 8 + Odoo Extensions)

**✅ DO**:
```python
# Use clear variable names
customer_name = record.partner_id.name
offer_price = record.price

# Use type hints where applicable
def action_accept_offer(self) -> None:
    """Accept the offer with proper documentation."""
    self.status = 'accepted'

# Keep functions small and focused
def _compute_best_offer(self):
    """Calculate best offer - less than 20 lines."""
    for record in self:
        prices = record.offer_ids.mapped('price')
        record.best_offer = max(prices) if prices else 0.0

# Use snake_case for functions and variables
def _check_price_positive(self):  # ✅ Good
    pass

def CheckPricePositive(self):  # ❌ Bad (use snake_case)
    pass
```

**❌ DON'T**:
```python
# Don't use single letter variables
p = record.price  # ❌ Unclear

# Don't have extremely long functions (>50 lines)
def complex_method(self):  # ❌ Too much logic
    # 100+ lines of code
    pass

# Don't hardcode values
if status == 'pending':  # Could be constant
    pass

# Don't nest more than 3 levels
if condition1:
    if condition2:
        if condition3:  # ❌ Too nested
            if condition4:  # ❌ Even worse
                pass
```

### 2. Code Organization

**✅ DO**:
```python
# Use clear sections in model files
class Property(models.Model):
    # Section 1: Model metadata
    _name = 'estate.property'
    _description = 'Real Estate Property'
    _order = 'name DESC'
    
    # Section 2: Field definitions (grouped by type)
    # --- Basic Information
    name = fields.Char(required=True)
    description = fields.Text()
    
    # --- Financial Fields
    expected_price = fields.Monetary()
    best_offer = fields.Monetary(compute='_compute_best_offer', store=True)
    
    # --- Relationships
    type_id = fields.Many2one('estate.property.type')
    offer_ids = fields.One2many('estate.property.offers', 'property_id')
    
    # Section 3: Constraints
    @api.constrains('expected_price')
    def _check_expected_price(self):
        pass
    
    # Section 4: Computations
    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        pass
    
    # Section 5: CRUD methods
    def create(self, vals_list):
        pass
    
    def write(self, vals):
        pass
    
    # Section 6: Business logic methods
    def action_sold(self):
        pass
    
    def action_cancel(self):
        pass
```

### 3. Import Organization

**✅ DO**:
```python
# Standard library imports
from datetime import timedelta
import logging

# Third-party imports
from reportlab.lib import colors

# Odoo imports
from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError
from odoo.tools import float_compare

# Module imports
from . import utils

logger = logging.getLogger(__name__)
```

**❌ DON'T**:
```python
# Don't mix import orders
from odoo import models
from datetime import timedelta
from odoo.exceptions import ValidationError
import logging

# Don't use wildcard imports
from odoo import *  # ❌ Unclear what imported

# Don't import unused modules
from reportlab import *  # ❌ If not used
```

---

## File Organization

### Proper Directory Structure

```
real_estate_ads/
├── models/
│   ├── __init__.py          ← Must exist
│   ├── property.py          ← One model per file
│   ├── property_offers.py
│   ├── property_type.py
│   └── property_tags.py
├── views/
│   ├── property_view.xml
│   ├── property_offer_view.xml
│   ├── property_type_view.xml
│   ├── property_tag_view.xml
│   └── menu_items.xml
├── security/
│   ├── real_estate_ads_groups.xml
│   ├── ir.model.access.csv
│   └── ir_rule_offer.xml
├── static/
│   ├── description/
│   │   └── icon.png         ← Module icon (recommended)
│   ├── css/
│   └── js/
├── report/
│   └── (custom reports if needed)
├── data/
│   └── default_data.xml
├── demo/
│   ├── demo_data.xml
│   └── demo_offers.xml
├── tests/                    ← ✅ MUST HAVE
│   ├── __init__.py
│   ├── test_property.py
│   ├── test_offers.py
│   └── test_security.py
├── __init__.py              ← Import models
├── __manifest__.py          ← Module configuration
└── README.md                ← ✅ MUST HAVE
```

### File Naming Conventions

**✅ DO**:
```
property.py           → 'estate.property' model
property_offers.py    → 'estate.property.offers' model
property_views.xml    → Views for property
ir_rule_offer.xml     → Record rules for offers
test_property.py      → Tests for property model
```

**❌ DON'T**:
```
Property.py           → Use lowercase
prop.py               → Don't abbreviate
models.py             → Don't group multiple models
views_all.xml         → Be specific about content
```

---

## Model Best Practices

### 1. Model Declaration

**✅ DO**:
```python
class Property(models.Model):
    """Real Estate Property - Main model for managing properties."""
    
    _name = 'estate.property'
    _description = 'Real Estate Property'
    _order = 'name DESC'
    _table = 'estate_property'  # Optional but recommended
    
    # Constraints to enforce data integrity
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Property name must be unique'),
        ('price_positive', 'check(expected_price >= 0)', 'Price cannot be negative'),
    ]
```

**❌ DON'T**:
```python
class Property(models.Model):
    _name = 'estate.property'
    # Missing description
    # Missing order
    # Missing docstring
```

### 2. Field Declarations

**✅ DO**:
```python
# Use meaningful field names
expected_price = fields.Monetary(
    string='Expected Price',          # User-friendly label
    currency_field='currency_id',
    required=True,                    # Explicit about requirements
    help='Initial asking price'       # Context for users
)

# Use proper field types
status = fields.Selection(
    [
        ('new', 'New'),
        ('received', 'Offer Received'),
        ('accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('cancel', 'Canceled'),
    ],
    string='Status',
    default='new',
    required=True                     # Selection should require value
)

# Group related fields with comments
# --- Address Information
postcode = fields.Char(string='Postcode')
street = fields.Char(string='Street')

# --- Physical Details
bedrooms = fields.Integer(string='Bedrooms')
living_area = fields.Integer(string='Living Area')
```

**❌ DON'T**:
```python
# Don't have unclear field names
p = fields.Char()  # What is p?
x = fields.Integer()  # Meaningless

# Don't use Char when better type exists
price = fields.Char()  # ❌ Should be Monetary or Float
active = fields.Char()  # ❌ Should be Boolean

# Don't forget string (label)
expected_price = fields.Monetary()  # ❌ No label

# Don't miss help text on complex fields
state = fields.Selection([('a', 'A'), ('b', 'B')])  # ❌ No help
```

### 3. Relationship Best Practices

**✅ DO**:
```python
# Many2One - Always specify ondelete
type_id = fields.Many2one(
    'estate.property.type',
    string='Property Type',
    ondelete='restrict'              # Prevent deletion with properties
)

# One2Many - Use reverse field for automatic backref
offer_ids = fields.One2many(
    'estate.property.offers',
    'property_id',                   # Reverse field name
    string='Offers'
)

# Many2Many - Proper configuration
tag_ids = fields.Many2many(
    'estate.property.tags',
    'estate_property_tags_rel',      # Junction table name
    'property_id',
    'tag_id',
    string='Property Tags'
)

# Related field for convenience
buyer_phone = fields.Char(
    string='Buyer Phone',
    related='buyer_id.phone',        # Chain of relations
    readonly=True                    # Don't edit through related
)
```

**❌ DON'T**:
```python
# Don't specify ondelete='cascade' lightly
type_id = fields.Many2one(
    'estate.property.type',
    ondelete='cascade'               # ❌ Deletes property if type deleted!
)

# Don't forget reverse field name
offer_ids = fields.One2many(
    'estate.property.offers',
    # ❌ Missing 'property_id'
)

# Don't use related for editable fields
buyer_phone = fields.Char(
    related='buyer_id.phone'         # ❌ Can't edit through here
)
```

---

## Business Logic

### 1. Validation Patterns

**✅ DO**:
```python
@api.constrains('expected_price')
def _check_expected_price_positive(self):
    """Constraint: expected price must be non-negative."""
    for record in self:
        if record.expected_price and record.expected_price < 0:
            raise ValidationError(
                _('Expected price for "%s" must be non-negative') % record.name
            )

# Complex multi-field validation
@api.constrains('price', 'validity')
def _check_offer_terms(self):
    """Validate offer has reasonable terms."""
    for record in self:
        if record.price <= 0:
            raise ValidationError(_('Offer price must be greater than 0'))
        if record.validity <= 0:
            raise ValidationError(_('Offer validity must be greater than 0 days'))
```

**❌ DON'T**:
```python
# Don't validate in write/create
def write(self, vals):
    for record in self:
        if record.price < 0:  # ❌ Should use @api.constrains
            raise ValidationError('...')
    return super().write(vals)

# Don't compare without null check
if record.price < 100:  # ❌ What if price is None?
    pass

# Don't use generic error messages
raise ValidationError('Invalid')  # ❌ User won't know what's wrong
```

### 2. Computed Fields

**✅ DO**:
```python
# Stored computed field (searchable/sortable)
total_area = fields.Integer(
    string='Total Area',
    compute='_compute_total_area',
    store=True,                      # ✅ Store for searching
    help='Living area + garden area'
)

@api.depends('living_area', 'garden_area')
def _compute_total_area(self):
    """Total area from living and garden areas."""
    for record in self:
        record.total_area = (record.living_area or 0) + (record.garden_area or 0)

# Non-stored for display only
offer_count = fields.Integer(
    string='Number of Offers',
    compute='_compute_offer_count'   # ✅ Not stored, recalc on load
)

@api.depends('offer_ids')
def _compute_offer_count(self):
    """Count offers for display."""
    for record in self:
        record.offer_count = len(record.offer_ids)

# Context-dependent field
is_manager = fields.Boolean(
    compute='_compute_is_manager'
)

@api.depends_context('uid')
def _compute_is_manager(self):
    """Check if current user is manager."""
    for record in self:
        record.is_manager = self.env.user.has_group(
            'module.group_manager'
        )
```

**❌ DON'T**:
```python
# Don't compute non-searchable fields as stored
status_display = fields.Char(
    compute='_compute_status_display',
    store=True  # ❌ Wastes space, never searched
)

# Don't depend on unrelated fields
best_offer = fields.Monetary(
    compute='_compute_best_offer'
)

@api.depends('all_fields')  # ❌ Recalcs too often
def _compute_best_offer(self):
    pass

# Don't ignore None values
total = record.field1 + record.field2  # ❌ Error if either is None
```

---

## Security Best Practices

### 1. Access Control

**✅ DO**:
```python
# Check permissions before actions
def action_accept_offer(self):
    """Accept offer - only sales/managers allowed."""
    
    # Check if user has permission
    if not self.env.user.has_group('module.group_property_sales'):
        raise AccessError(_('You do not have permission to accept offers'))
    
    # Perform action
    self.write({'status': 'accepted'})

# Use try-except for permission errors
try:
    self.env['model'].create(vals)
except AccessError as e:
    logger.warning(f"Access denied: {e}")
    raise
```

**❌ DON'T**:
```python
# Don't skip permission checks
def action_delete_property(self):
    self.unlink()  # ❌ No permission check

# Don't use plain except
try:
    record.write(vals)
except:  # ❌ Catches everything including programming errors
    pass

# Don't allow SQL injection
query = f"SELECT * FROM {table} WHERE id = {id}"  # ❌ SQL injection!
```

### 2. Record-Level Security Rules

**✅ DO**:
```xml
<!-- User only sees their own records -->
<record id="property_user_rule" model="ir.rule">
    <field name="name">Property User - Own Records Only</field>
    <field name="model_id" ref="model_estate_property"/>
    <field name="domain_force">[('create_uid', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('group_property_user'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_unlink" eval="False"/>
</record>

<!-- Manager sees all -->
<record id="property_manager_rule" model="ir.rule">
    <field name="name">Property Manager - All Records</field>
    <field name="model_id" ref="model_estate_property"/>
    <field name="domain_force">[(1, '=', 1)]</field>  <!-- Always true -->
    <field name="groups" eval="[(4, ref('group_property_manager'))]"/>
</record>
```

**❌ DON'T**:
```xml
<!-- Don't use complex domain without explaining -->
<field name="domain_force">[('partner_id', 'in', user.partner_id.commercial_partner_id.partner_ids.ids)]</field>

<!-- Don't grant more permissions than needed -->
<field name="perm_unlink" eval="True"/>  <!-- If not absolutely needed -->
```

---

## View and UI Standards

### 1. Form View Best Practices

**✅ DO**:
```xml
<form string="Property">
    <!-- Use Header for status/buttons -->
    <header>
        <button name="action_sold" 
            string="Mark as Sold" 
            type="object" 
            class="btn-primary"
            groups="module.group_property_manager"/>
        <field name="state" widget="statusbar"/>
    </header>
    
    <sheet>
        <!-- Organize with groups -->
        <group name="main_info" string="Main Information">
            <!-- Left column -->
            <field name="name" required="1"/>
            <field name="type_id"/>
            
            <!-- Right column -->
            <field name="expected_price"/>
            <field name="postcode"/>
        </group>
        
        <!-- Use notebook for tabs -->
        <notebook>
            <page string="Details">
                <group>
                    <field name="description"/>
                    <field name="bedrooms"/>
                </group>
            </page>
            
            <page string="Offers">
                <!-- One2Many inline editing -->
                <field name="offer_ids">
                    <list editable="bottom">
                        <field name="price"/>
                        <field name="status"/>
                    </list>
                </field>
            </page>
        </notebook>
    </sheet>
</form>
```

**❌ DON'T**:
```xml
<!-- Don't have too many fields without grouping -->
<form>
    <field name="f1"/><field name="f2"/><field name="f3"/>
    <field name="f4"/><field name="f5"/><field name="f10"/>
    <!-- Overwhelming -->
</form>

<!-- Don't use outdated attrs= -->
<field name="price" attrs="{'readonly': [('state', '=', 'sold')]}"/>
<!-- Use invisible= instead -->

<!-- Don't forget labels on buttons -->
<button name="action" type="object"/>  <!-- ❌ No string -->
```

---

## Database and Performance

### 1. Query Optimization

**✅ DO**:
```python
# Use search with domain (filtered at DB level)
properties = self.env['estate.property'].search([
    ('state', '=', 'new'),
    ('expected_price', '>', 100000)
])  # ✅ Filtered at database

# Use mapped() for extracting values
prices = properties.mapped('price')  # ✅ Efficient

# Use filtered() for Python-side filtering (small datasets only)
high_price = properties.filtered(lambda p: p.price > 100000)

# Use limit and offset for pagination
first_10 = self.env['estate.property'].search([], limit=10, offset=0)
```

**❌ DON'T**:
```python
# Don't load all records then filter in Python
all_props = self.env['estate.property'].search([])
for prop in all_props:  # ❌ Loads all!
    if prop.state == 'new':
        # Use domain in search instead

# Don't use nested loops for related records
for property in properties:
    for offer in property.offer_ids:  # ❌ N+1 query problem
        print(offer.price)

# Use mapped() instead
prices = properties.mapped('offer_ids.price')
```

### 2. Compute Fields Optimization

**✅ DO**:
```python
# Store computed fields that are frequently searched/sorted
total_area = fields.Integer(
    compute='_compute_total_area',
    store=True  # ✅ Searchable and sortable
)

# Don't store if rarely used
display_status = fields.Char(
    compute='_compute_display_status'
    # No store - recalc on load only
)

# Use @api.depends carefully - depends only on necessary fields
@api.depends('living_area', 'garden_area')  # ✅ Only these
def _compute_total_area(self):
    for record in self:
        record.total_area = (record.living_area or 0) + (record.garden_area or 0)
```

---

## Testing Standards

### 1. Unit Tests for Critical Logic

**✅ DO**:
```python
# tests/test_offers.py

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestOfferWorkflow(TransactionCase):
    """Test offer creation and acceptance."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test property
        self.property = self.env['estate.property'].create({
            'name': 'Test House',
            'expected_price': 500000,
        })
        
        # Create test offer
        self.offer = self.env['estate.property.offers'].create({
            'property_id': self.property.id,
            'price': 480000,
            'validity': 7,
            'partner_id': self.env.user.partner_id.id,
        })
    
    def test_offer_creation(self):
        """Test offer is created with correct defaults."""
        self.assertEqual(self.offer.status, 'pending')
        self.assertEqual(self.offer.property_id, self.property)
    
    def test_offer_price_validation(self):
        """Test offer price must be positive."""
        with self.assertRaises(ValidationError):
            self.env['estate.property.offers'].create({
                'property_id': self.property.id,
                'price': -1000,  # Negative - should fail
                'validity': 7,
                'partner_id': self.env.user.partner_id.id,
            })
    
    def test_accept_offer(self):
        """Test accepting offer updates states."""
        self.offer.action_accept_offer()
        
        self.assertEqual(self.offer.status, 'accepted')
        self.assertEqual(self.property.state, 'accepted')
```

**❌ DON'T**:
```python
# Don't manually update database in tests
self.env.cr.execute("UPDATE offer SET status='accepted'")  # ❌ Bypass ORM

# Don't test unrelated things
def test_everything(self):
    # Create, test, delete, check, update - too much ❌

# Don't commit in tests
self.env.cr.commit()  # ❌ Tests auto-rollback
```

---

## Error Handling

### 1. Proper Exception Usage

**✅ DO**:
```python
from odoo.exceptions import ValidationError, AccessError, UserError

# ValidationError - Data validation failure
if record.price <= 0:
    raise ValidationError(_('Price must be greater than 0'))

# AccessError - Permission denied
if not self.env.user.has_group('group_sales'):
    raise AccessError(_('You do not have permission to accept offers'))

# UserError - Business logic violation (user-friendly)
if record.property_id.state != 'new':
    raise UserError(_(
        'Cannot create offer for property in state "%s"'
    ) % record.property_id.state)

# Log important events
logger.info(f"Offer {record.id} accepted by {self.env.user.name}")
```

**❌ DON'T**:
```python
# Don't use generic Exception
raise Exception('Error')  # ❌ Unclear to user

# Don't forget context
raise ValidationError('Invalid')  # ❌ Which field?

# Don't catch too broad
try:
    dangerous_operation()
except:  # ❌ Catches everything
    pass

# Don't print debug info - use logging
print(f"Debug: {record}")  # ❌ Use logger.info()
```

---

## Documentation Standards

### 1. Code Comments and Docstrings

**✅ DO**:
```python
def action_accept_offer(self):
    """
    Accept the offer and update property state.
    
    This method:
    1. Validates user has sales/manager permission
    2. Prevents multiple accepted offers per property
    3. Refuses all other offers automatically
    4. Updates property state to 'accepted'
    
    Raises:
        AccessError: If user not in sales/manager group
        ValidationError: If property already has accepted offer
    
    Returns:
        None
    """
    # Validate permissions
    if not self.env.user.has_group('module.group_property_sales'):
        raise AccessError(_('Permission denied'))
    
    # Check for existing accepted offer
    for offer in self:
        existing = offer.property_id.offer_ids.filtered(
            lambda o: o.status == 'accepted' and o.id != offer.id
        )
        if existing:
            raise ValidationError(_('Property already has accepted offer'))
    
    # Accept this offer
    self.write({'status': 'accepted'})
    
    # Refuse other offers
    for offer in self:
        other_offers = offer.property_id.offer_ids - offer
        other_offers.write({'status': 'refused'})
```

**❌ DON'T**:
```python
def action_accept_offer(self):  # ❌ No docstring
    # This accepts the offer  # ❌ Obvious comment
    self.write({'status': 'accepted'})
    # Update property  # ❌ What does this do?
    self.property_id.state = 'accepted'

# Don't have comments that duplicate code
name = fields.Char()  # Set the name field  # ❌ Obvious
```

---

## Code Review Checklist

### Before Deployment

**Code Quality**:
- [ ] All code follows PEP 8 style
- [ ] No hardcoded values (use constants/settings)
- [ ] Functions are focused and < 50 lines
- [ ] No code duplication (DRY principle)
- [ ] Imports are organized and minimal
- [ ] No print() statements (use logging)

**Functionality**:
- [ ] All features implemented per requirements
- [ ] Edge cases handled (None, empty lists, etc.)
- [ ] No SQL injection vulnerabilities
- [ ] Proper error messages for users
- [ ] All code paths tested

**Security**:
- [ ] Permission checks on all sensitive actions
- [ ] Record rules properly defined
- [ ] ACL entries correct
- [ ] No hardcoded credentials
- [ ] Input validation on all user input

**Performance**:
- [ ] Search queries use domain filtering
- [ ] No N+1 query problems
- [ ] Stored computed fields when needed
- [ ] Indexes on frequently searched fields
- [ ] Heavy operations in background jobs

**Documentation**:
- [ ] All models have docstrings
- [ ] All methods have docstrings
- [ ] Complex logic is explained
- [ ] README.md is complete
- [ ] Views are commented

**Testing**:
- [ ] Unit tests exist for critical logic
- [ ] Tests pass locally
- [ ] No test data left in database
- [ ] Edge cases tested

**Deployment**:
- [ ] __manifest__.py is correct
- [ ] All data files are in place
- [ ] Demo data included (if applicable)
- [ ] External dependencies listed
- [ ] No debug code or commented-out code

---

## Production Deployment Checklist

### Pre-Deployment

- [ ] All code reviewed and approved
- [ ] All tests passing (100% of critical paths)
- [ ] No console errors or warnings
- [ ] Performance tested with realistic data
- [ ] Security audit completed
- [ ] Database migrations tested
- [ ] Backup strategy confirmed

### Deployment

- [ ] Database backed up
- [ ] Staging environment tested
- [ ] Deployment plan documented
- [ ] Rollback plan ready
- [ ] Stakeholders notified
- [ ] Monitoring configured

### Post-Deployment

- [ ] All features working as expected
- [ ] No critical errors in logs
- [ ] Performance metrics normal
- [ ] Users trained if needed
- [ ] Documentation updated
- [ ] Deployment logged

---

## Anti-Patterns to Avoid

### 1. Common Mistakes

**❌ DON'T DO**:

```python
# 1. Circular imports
# models/property.py
from .property_offers import PropertyOffers  # Can cause issues

# 2. Modifying in loop without understanding implications
for offer in self.offer_ids:
    offer.property_id.state = 'received'  # Updates multiple times!
# Better: do once after loop

# 3. Comparing datetime/date with strings
if record.date > '2024-01-01':  # ❌ Type mismatch
    pass

# 4. Using always-true conditions
if 1 == 1:  # ❌ Obviously true
    pass

# 5. Ignoring exceptions silently
try:
    risky_operation()
except:
    pass  # ❌ Silently failing

# 6. Creating records in loop without batch
for vals in big_list:  # ❌ Creates record one by one
    self.env['model'].create(vals)
# Better: self.env['model'].create(big_list)

# 7. Storing mutable default values
tags = fields.Many2many(default=[1, 2, 3])  # ❌ Shared between records
# Better: Use callable
tags = fields.Many2many(default=lambda self: [])
```

---

## Module Improvement Plan for Real Estate Ads

### Phase 1: Immediate Improvements (Quick Wins)

1. **Add Unit Tests**
   - Test property creation
   - Test offer workflows
   - Test security rules

2. **Improve Error Messages**
   - Use descriptive ValidationError messages
   - Translate all user-visible text

3. **Add Logging**
   - Log offer acceptance
   - Log property state changes
   - Track important business events

### Phase 2: Mid-Term Improvements

1. **Performance Optimization**
   - Add indexes on frequently searched fields
   - Optimize computed fields
   - Profile slow operations

2. **Enhanced Documentation**
   - Add docstrings to all methods
   - Create admin guide
   - Create user guide

3. **Extended Testing**
   - Integration tests
   - Load testing
   - Security testing

### Phase 3: Long-Term Enhancements

1. **Advanced Features**
   - Bulk operations
   - Reporting/analytics
   - Import/export

2. **User Experience**
   - Custom dashboards
   - Mobile optimization
   - Notifications

3. **Scaling**
   - Background jobs for heavy operations
   - Caching strategy
   - Database optimization

---

## Standard Configuration for Production

### __manifest__.py Best Practices

```python
{
    'name': 'Real Estate Ads',
    'version': '19.0.1.0.0',
    'category': 'Administration',
    'summary': 'Comprehensive real estate property and offer management',
    'author': 'Your Company',
    'website': 'https://yourwebsite.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],  # Minimal dependencies
    'data': [
        # Load security first
        'security/real_estate_ads_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule_offer.xml',
        # Then views
        'views/property_view.xml',
        'views/property_offer_view.xml',
        'views/property_type_view.xml',
        'views/property_tag_view.xml',
        'views/menu_items.xml',
        # Then data
        'data/property_type.xml',
    ],
    'demo': [
        'demo/property_tag.xml',
        'demo/property.xml',
        'demo/property_offer.xml',
    ],
    'images': ['static/description/icon.png'],
    'external_dependencies': {
        'python': [],  # External Python packages if needed
        'bin': [],     # External executables if needed
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',  # Optional: initialization
    'post_migrate_hook': 'post_migrate_hook',  # Optional: migrations
}
```

---

## Conclusion

### Key Takeaways

✅ **DO**:
- Write clean, readable code
- Use proper validation and error handling
- Test critical functionality
- Document complex logic
- Think about security from start
- Optimize for performance
- Follow Odoo conventions

❌ **DON'T**:
- Skip error handling
- Ignore security
- Hardcode values
- Leave code untested
- Write unclear code
- Optimize prematurely
- Ignore conventions

---

**Production-Ready Status**: When you can check all items in the Code Review Checklist, your module is ready for production deployment.

**Version**: 1.0  
**Last Updated**: May 21, 2026  
**Odoo Version**: 19.0

