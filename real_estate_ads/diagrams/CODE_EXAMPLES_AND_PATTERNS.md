# Real Estate Ads - Code Examples and Patterns Guide

This document provides practical code examples and design patterns used throughout the real_estate_ads module.

---

## Table of Contents

1. [Common Code Patterns](#common-code-patterns)
2. [Field Definition Examples](#field-definition-examples)
3. [Computed Field Patterns](#computed-field-patterns)
4. [Validation Patterns](#validation-patterns)
5. [Business Logic Examples](#business-logic-examples)
6. [View Configuration Examples](#view-configuration-examples)
7. [Security Configuration Examples](#security-configuration-examples)

---

## Common Code Patterns

### Pattern 1: Loop Through Records

```python
# Iterate through a recordset
for record in self:
    # Process each record individually
    record.total_area = (record.living_area or 0) + (record.garden_area or 0)
```

**Why?** Models work with recordsets (multiple records), not single objects. Always loop.

**Example from code**:
```python
@api.depends('living_area', 'garden_area')
def _compute_total_area(self):
    for record in self:
        record.total_area = (record.living_area or 0) + (record.garden_area or 0)
```

### Pattern 2: Handle Optional Values with `or`

```python
# If field might be None or False
value = field_name or default_value

# Examples
record.total_area = (record.living_area or 0) + (record.garden_area or 0)
# If living_area is None, use 0 instead
```

**Why?** Python fields can be None, causing TypeError. `or` provides safe default.

### Pattern 3: Filter Recordsets

```python
# Get subset of records matching condition
filtered = recordset.filtered(lambda r: r.status == 'accepted')

# Real example from code
accepted = record.offer_ids.filtered(lambda o: o.status == 'accepted')
if accepted:
    record.selling_price = max(accepted.mapped('price'))
```

**Why?** More efficient than looping with if statements.

### Pattern 4: Map Values from Related Records

```python
# Extract values from relationship
prices = record.offer_ids.mapped('price')
# Result: [500000, 520000, 480000]

# Use in calculation
best_offer = max(prices) if prices else 0.0
```

**Why?** Pythonic way to extract field values from related records.

### Pattern 5: Check User Group

```python
# Check if user belongs to group
if self.env.user.has_group('real_estate_ads.group_property_manager'):
    # User is manager, allow action
    self.state = 'sold'
else:
    # User not manager, deny
    raise AccessError('Only Property Managers can mark as sold.')
```

**Why?** Enforce permissions at code level (in addition to UI/database).

---

## Field Definition Examples

### Simple Text Field

```python
name = fields.Char(string='Name', required=True)
```

**Attributes**:
- `string`: Label shown in UI
- `required=True`: User must enter value
- Default type: Char(255)

### Integer Field

```python
bedrooms = fields.Integer(string='Bedrooms')
```

**Use when**: Counting items (no decimals)

### Boolean Field

```python
garage = fields.Boolean(string='Garage', default=False)

# In form, displays as checkbox
```

### Date Field

```python
date_availability = fields.Date(string='Available From')

# In form, displays as calendar picker
```

### Monetary Field

```python
expected_price = fields.Monetary(
    string='Expected Price',
    currency_field='currency_id'  # Links to currency field
)
```

**Why separate from Float?**
- Handles currency formatting
- Validates decimal places
- Integrates with multi-currency

### Selection Field (Dropdown)

```python
state = fields.Selection(
    [
        ('new', 'New'),
        ('received', 'Offer Received'),
        ('accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('cancel', 'Canceled')
    ],
    string='Status',
    default='new'
)
```

**Structure**: [('value', 'Display Label'), ...]

### Many2One (Foreign Key)

```python
type_id = fields.Many2one(
    'estate.property.type',  # Related model
    string='Property Type'
)
```

**Creates**: Foreign key relationship (many property → one type)

```python
# Access related record
property.type_id.name  # Get type name
property.type_id.id    # Get type ID
```

### One2Many (Reverse ForeignKey)

```python
offer_ids = fields.One2many(
    'estate.property.offers',  # Related model
    'property_id',             # Field that points back
    string='Offers'
)
```

**Creates**: Container for related records

```python
# Access related records
property.offer_ids              # Recordset of offers
len(property.offer_ids)         # Count
property.offer_ids[0]           # First offer
property.offer_ids.mapped('price')  # All prices
```

### Many2Many (Junction Table)

```python
tag_ids = fields.Many2many(
    'estate.property.tags',  # Related model
    string='Property Tags'
)
```

**Creates**: Automatic junction table

```python
# Access related records
property.tag_ids                # All tags
property.tag_ids.mapped('name') # All tag names
```

### Related Field (Convenience)

```python
# Shows buyer's phone without navigating
phone = fields.Char(
    string='Phone',
    related='buyer_id.phone',  # Follows chain: buyer_id.phone
    readonly=True              # Cannot edit here
)
```

**Use when**: Need to display nested field values without scrolling

### Computed Field (Auto-Calculated)

```python
total_area = fields.Integer(
    string='Total Area',
    compute='_compute_total_area',  # Method name
    store=True,                      # Save to DB for searching
    help='Total area in sqm (living_area + garden_area)'
)

@api.depends('living_area', 'garden_area')
def _compute_total_area(self):
    for record in self:
        record.total_area = (record.living_area or 0) + (record.garden_area or 0)
```

---

## Computed Field Patterns

### Pattern 1: Basic Computed Field (Not Stored)

```python
offer_count = fields.Integer(
    string="Offer Count",
    compute='_compute_offer_count'
)

@api.depends('offer_ids')
def _compute_offer_count(self):
    for record in self:
        record.offer_count = len(record.offer_ids)
```

**Characteristics**:
- Recalculated every time called
- NOT stored in database
- Cannot search/sort by this field
- Use for: Display only

### Pattern 2: Stored Computed Field

```python
best_offer = fields.Monetary(
    string='Best Offer',
    compute='_compute_best_offer',
    store=True,  # ← Save to database
    currency_field='currency_id',
    help='Highest offer price received for the property'
)

@api.depends('offer_ids.price')
def _compute_best_offer(self):
    for record in self:
        offer_prices = record.offer_ids.mapped('price')
        record.best_offer = max(offer_prices) if offer_prices else 0.0
```

**Characteristics**:
- Stored in database
- Searchable and sortable
- Better performance for large datasets
- Recalculated on save
- Use for: Reports, listings, filtering

### Pattern 3: Computed Field with Context Dependency

```python
is_manager = fields.Boolean(
    string='Is Manager',
    compute='_compute_is_manager'
)

@api.depends_context('uid')  # ← Watch user context
def _compute_is_manager(self):
    for record in self:
        record.is_manager = self.env.user.has_group(
            'real_estate_ads.group_property_manager'
        )
```

**Characteristics**:
- Recalculates when user changes
- Values differ per user
- Use for: Dynamic UI control, permissions

### Pattern 4: Computed Field with Inverse (Editable)

```python
deadline = fields.Date(
    string='Deadline',
    compute='_compute_deadline',
    inverse='_inverse_deadline',
    store=True
)

@api.depends('validity', 'creation_date')
def _compute_deadline(self):
    for record in self:
        if record.creation_date:
            days = max(record.validity or 1, 1)
            record.deadline = record.creation_date + timedelta(days=days)

def _inverse_deadline(self):
    """When user edits deadline, update validity"""
    for record in self:
        record.validity = record._compute_validity_from_deadline(
            record.creation_date,
            record.deadline
        )
```

**Characteristics**:
- Can be edited by user
- Inverse method updates related field
- Maintains data consistency
- Use for: Auto-calculated but user-overridable

---

## Validation Patterns

### Pattern 1: Field Constraint

```python
@api.constrains('expected_price')
def _check_expected_price_non_negative(self):
    """Block negative expected price values at the application level."""
    for record in self:
        if record.expected_price is not None and record.expected_price < 0:
            raise ValidationError('Expected price must be non-negative.')
```

**Execution**: When saving the record

**Result**: Error message shown to user

### Pattern 2: Multi-Field Constraint

```python
@api.constrains('price', 'validity')
def _validate_offer_terms(self):
    """Validate offer has valid terms"""
    for record in self:
        if record.price <= 0:
            raise ValidationError('Price must be > 0')
        if record.validity <= 0:
            raise ValidationError('Validity must be > 0 days')
```

### Pattern 3: Complex Business Logic Validation

```python
def action_accept_offer(self):
    """Accept the offer, update property state, refuse other offers."""
    # Validation 1: Check permissions
    if not (self.env.user.has_group('group_property_sales') or 
            self.env.user.has_group('group_property_manager')):
        raise AccessError('You do not have the rights to accept offers.')
    
    # Validation 2: Check business logic
    for offer in self:
        if offer.property_id:
            already_accepted = offer.property_id.offer_ids.filtered(
                lambda o: o.status == 'accepted' and o.id != offer.id
            )
            if already_accepted:
                raise ValidationError(
                    'This property already has an accepted offer. '
                    'Refuse the existing accepted offer before accepting another.'
                )
    
    # If all validations pass, proceed with action
    self.write({'status': 'accepted'})
    # ... rest of logic
```

---

## Business Logic Examples

### Example 1: Offer Acceptance Workflow

```python
def action_accept_offer(self):
    """Accept the offer, update the property state, and refuse other offers."""
    
    # Step 1: Verify permissions
    if not (self.env.user.has_group('real_estate_ads.group_property_sales') or 
            self.env.user.has_group('real_estate_ads.group_property_manager')):
        raise AccessError('You do not have the rights to accept offers.')
    
    # Step 2: Verify only one accepted offer per property
    for offer in self:
        if offer.property_id:
            already_accepted = offer.property_id.offer_ids.filtered(
                lambda o: o.status == 'accepted' and o.id != offer.id
            )
            if already_accepted:
                raise ValidationError(
                    'This property already has an accepted offer (ID: %s). '
                    'Refuse the existing accepted offer before accepting another.' 
                    % already_accepted[0].id
                )
    
    # Step 3: Accept this offer and refuse others
    self.write({'status': 'accepted'})
    for offer in self:
        if offer.property_id:
            # Update property state
            offer.property_id.state = 'accepted'
            
            # Refuse all other offers
            other_offers = offer.property_id.offer_ids.filtered(
                lambda o: o.id != offer.id
            )
            other_offers.write({'status': 'refused'})
```

**Flow Execution**:
```
1. User clicks "Accept" button
2. Permissions checked (AccessError if fail)
3. Business logic checked (ValidationError if fail)
4. Offer marked accepted
5. Property marked accepted
6. All other offers marked refused
7. Computed fields recalculate (selling_price updates)
8. Form refreshes with new state
```

### Example 2: Auto-Link Offer to User

```python
@api.model_create_multi
def create(self, vals_list):
    """Auto-link offers to the current user's partner if not provided."""
    for vals in vals_list:
        # If partner_id not specified
        if not vals.get('partner_id') and self.env.user.partner_id:
            # Auto-populate with current user's partner
            vals['partner_id'] = self.env.user.partner_id.id
    
    # Call parent create with updated values
    return super().create(vals_list)
```

**When it runs**: When user creates a new offer

**What it does**:
1. Check if partner_id provided
2. If not, use current user's partner
3. Continue normal record creation

**Result**: Offers automatically linked to who created them

---

## View Configuration Examples

### Example 1: Property Form Field with Conditional Readonly

```xml
<!-- Field editable only for managers -->
<field name="name" 
    widget="char_emojis" 
    placeholder="Property Name"
    readonly="not is_manager"/>
```

**How it works**:
- If is_manager = True: readonly = False (editable)
- If is_manager = False: readonly = True (read-only)

### Example 2: Field Hidden from Non-Managers

```xml
<!-- Type field only visible to managers -->
<field name="type_id" 
    invisible="not is_manager"/>
```

**How it works**:
- If is_manager = True: invisible = False (shown)
- If is_manager = False: invisible = True (hidden)

### Example 3: Button Visible Only for Sales/Manager

```xml
<!-- Accept button only shown for sales group -->
<button name="action_accept_offer" 
    string="Accept" 
    type="object" 
    class="btn-success" 
    groups="real_estate_ads.group_property_sales"
    invisible="status != 'pending' or property_state not in ['new', 'received']"/>
```

**Dual Criteria**:
1. `groups="real_estate_ads.group_property_sales"` - Must be in group
2. `invisible="status != 'pending' or property_state not in ['new', 'received']"` - Logical condition

**Logical Expression Breakdown**:
```
Show button IF:
  status == 'pending' AND property_state IN ['new', 'received']

Hide button IF:
  status != 'pending' OR property_state NOT IN ['new', 'received']
```

### Example 4: One2Many Inline Editing

```xml
<field name="offer_ids">
    <list editable="bottom" 
        decoration-success="status == 'accepted'" 
        decoration-danger="status == 'refused'">
        
        <field name="price"/>
        <field name="partner_id"/>
        <field name="creation_date"/>
        <field name="validity"/>
        <field name="deadline" widget="remaining_days"/>
        <field name="status" nolabel="1" readonly="True"/>
        
        <!-- Action buttons -->
        <button name="action_accept_offer" 
            string="Accept" 
            type="object" 
            class="btn-success" 
            groups="real_estate_ads.group_property_sales"
            invisible="status != 'pending' or property_state not in ['new', 'received']"/>
    </list>
</field>
```

**Features**:
- `editable="bottom"` - Add new row at bottom
- `decoration-success="..."` - Green highlight if accepted
- `decoration-danger="..."` - Red highlight if refused
- Inline add/edit without opening form
- Full CRUD in single view

### Example 5: Conditional Field Visibility Based on Another Field

```xml
<!-- Garden area only shown if garden=true -->
<field name="garden_area" 
    invisible="not garden"/>

<!-- Garden orientation only shown if garden=true -->
<field name="garden_orientation" 
    invisible="not garden" 
    widget="selection_badge"/>
```

**Logic**:
- If garden = True: Show garden_area and garden_orientation
- If garden = False: Hide garden_area and garden_orientation

---

## Security Configuration Examples

### Example 1: Security Group Definition

```xml
<!-- File: security/real_estate_ads_groups.xml -->

<!-- Base user group -->
<record id="group_property_user" model="res.groups">
    <field name="name">Property User</field>
    <field name="sequence">10</field>
    <field name="privilege_id" ref="res_groups_privilege_real_estate_ads"/>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
    <field name="comment">Read-only access to view properties and create/edit own offers.</field>
</record>

<!-- Sales group (implies user group) -->
<record id="group_property_sales" model="res.groups">
    <field name="name">Property Sales</field>
    <field name="sequence">20</field>
    <field name="privilege_id" ref="res_groups_privilege_real_estate_ads"/>
    <field name="implied_ids" eval="[(4, ref('real_estate_ads.group_property_user'))]"/>
    <field name="comment">Sales users can accept/refuse offers, manage all offers, and mark properties as sold/cancelled.</field>
</record>

<!-- Manager group (implies sales group) -->
<record id="group_property_manager" model="res.groups">
    <field name="name">Property Manager</field>
    <field name="sequence">30</field>
    <field name="privilege_id" ref="res_groups_privilege_real_estate_ads"/>
    <field name="implied_ids" eval="[(4, ref('real_estate_ads.group_property_sales'))]"/>
    <field name="comment">Full access to manage properties, types, tags, offers and all configurations.</field>
</record>
```

**Hierarchy Result**:
```
Manager has: group_property_manager + group_property_sales + group_property_user
Sales has: group_property_sales + group_property_user
User has: group_property_user
```

### Example 2: Access Control List

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink

# Property model permissions
access_estate_property_user,Property User Access,real_estate_ads.model_estate_property,real_estate_ads.group_property_user,1,0,0,0
access_estate_property_sales,Property Sales Access,real_estate_ads.model_estate_property,real_estate_ads.group_property_sales,1,1,1,0
access_estate_property_manager,Property Manager Access,real_estate_ads.model_estate_property,real_estate_ads.group_property_manager,1,1,1,1

# Property Type permissions (manager only)
access_estate_property_type_user,Property Type User Access,real_estate_ads.model_estate_property_type,real_estate_ads.group_property_user,1,0,0,0
access_estate_property_type_manager,Property Type Manager Access,real_estate_ads.model_estate_property_type,real_estate_ads.group_property_manager,1,1,1,1

# All groups can CRUD offers (row-level rules apply)
access_estate_property_offers_user,Property Offers User Access,real_estate_ads.model_estate_property_offers,real_estate_ads.group_property_user,1,1,1,1
access_estate_property_offers_sales,Property Offers Sales Access,real_estate_ads.model_estate_property_offers,real_estate_ads.group_property_sales,1,1,1,1
access_estate_property_offers_manager,Property Offers Manager Access,real_estate_ads.model_estate_property_offers,real_estate_ads.group_property_manager,1,1,1,1
```

**Interpretation**:
- 1 = permission granted
- 0 = permission denied
- Example row 1: User group can only READ estate.property

### Example 3: Record-Level Security Rule

```xml
<!-- File: security/ir_rule_offer.xml -->

<!-- Users can only see offers they created -->
<record id="property_offer_user_read_rule" model="ir.rule">
    <field name="name">Property Offer: User can read own offers</field>
    <field name="model_id" ref="real_estate_ads.model_estate_property_offers"/>
    <field name="domain_force">[('partner_id', '=', user.partner_id.id)]</field>
    <field name="groups" eval="[(4, ref('real_estate_ads.group_property_user'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="False"/>
    <field name="perm_create" eval="False"/>
    <field name="perm_unlink" eval="False"/>
</record>

<!-- Sales/Managers can see and manage all offers -->
<record id="property_offer_sales_rule" model="ir.rule">
    <field name="name">Property Offer: Sales and Manager can manage all offers</field>
    <field name="model_id" ref="real_estate_ads.model_estate_property_offers"/>
    <field name="domain_force">[(1, '=', 1)]</field>  <!-- Always true, no filtering -->
    <field name="groups" eval="[(4, ref('real_estate_ads.group_property_sales'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="True"/>
</record>
```

**How Record Rules Work**:
1. User tries to access record
2. System checks: Is user in the groups specified?
3. If yes: Apply the domain_force condition
4. Result: Automatically filters queries

---

## Common Mistakes and Solutions

### Mistake 1: Forgetting Loop in Computed Field

```python
# ❌ WRONG
@api.depends('living_area', 'garden_area')
def _compute_total_area(self):
    self.total_area = self.living_area + self.garden_area  # Fails if multiple records

# ✅ CORRECT
@api.depends('living_area', 'garden_area')
def _compute_total_area(self):
    for record in self:
        record.total_area = record.living_area + record.garden_area
```

### Mistake 2: Not Handling None Values

```python
# ❌ WRONG
total = record.living_area + record.garden_area  # Error if either is None

# ✅ CORRECT
total = (record.living_area or 0) + (record.garden_area or 0)
```

### Mistake 3: Forgetting self.write() for Multiple Records

```python
# ❌ WRONG - updates only last record
for offer in offers:
    offer.status = 'refused'

# ✅ CORRECT - updates all at once
offers.write({'status': 'refused'})
```

### Mistake 4: Not Checking Existence Before Accessing Related

```python
# ❌ WRONG - error if property_id is None
property.property_id.state = 'received'

# ✅ CORRECT
if offer.property_id:
    offer.property_id.state = 'received'
```

---

## Performance Optimization Tips

### Tip 1: Use store=True for Searchable Computed Fields

```python
# ❌ Slow - computes every time
total_area = fields.Integer(compute='_compute_total_area')

# ✅ Fast - stored, searchable
total_area = fields.Integer(
    compute='_compute_total_area',
    store=True
)
```

### Tip 2: Use mapped() Instead of Loop

```python
# ❌ Slower
prices = []
for offer in offers:
    prices.append(offer.price)

# ✅ Faster
prices = offers.mapped('price')
```

### Tip 3: Use filtered() for Conditions

```python
# ❌ Slower
accepted = [o for o in offers if o.status == 'accepted']

# ✅ Faster + Odoo-optimized
accepted = offers.filtered(lambda o: o.status == 'accepted')
```

---

## Testing Examples

### Test Valid Offer Creation

```python
def test_offer_creation(self):
    # Create property
    property = self.env['estate.property'].create({
        'name': 'Test House',
        'expected_price': 500000,
    })
    
    # Create offer
    offer = self.env['estate.property.offers'].create({
        'property_id': property.id,
        'partner_id': self.env.user.partner_id.id,
        'price': 480000,
        'validity': 7,
    })
    
    # Assertions
    self.assertEqual(offer.property_id, property)
    self.assertEqual(offer.status, 'pending')
    self.assertEqual(property.state, 'received')
```

### Test Offer Acceptance

```python
def test_accept_offer(self):
    # Setup
    property = self._create_property()
    offer1 = self._create_offer(property, 480000)
    offer2 = self._create_offer(property, 500000)
    
    # Accept offer1
    offer1.action_accept_offer()
    
    # Assertions
    self.assertEqual(offer1.status, 'accepted')
    self.assertEqual(offer2.status, 'refused')
    self.assertEqual(property.state, 'accepted')
    self.assertEqual(property.selling_price, 480000)
```

---

**End of Code Examples Guide**  
**Version**: 1.0  
**Date**: May 21, 2026

