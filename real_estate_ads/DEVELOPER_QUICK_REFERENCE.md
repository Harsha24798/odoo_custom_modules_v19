# Real Estate Ads - Developer Quick Reference Guide

A quick lookup guide for developers working on the real_estate_ads module.

---

## Quick Navigation

### Module Structure Map

```
real_estate_ads/
├── models/
│   ├── property.py              ← Main property model (144 lines)
│   ├── property_offers.py       ← Offers model (191 lines)
│   ├── property_type.py         ← Types (10 lines)
│   └── property_tags.py         ← Tags (11 lines)
├── views/
│   ├── property_view.xml        ← Form/List/Kanban views
│   ├── property_offer_view.xml  ← Offer views
│   ├── property_type_view.xml   ← Type views
│   ├── property_tag_view.xml    ← Tag views
│   └── menu_items.xml           ← Navigation menus
├── security/
│   ├── real_estate_ads_groups.xml   ← Role definitions
│   ├── ir.model.access.csv          ← Access control
│   └── ir_rule_offer.xml            ← Row-level rules
├── data/ & demo/
│   └── Default and sample data
└── __manifest__.py              ← Module configuration
```

---

## Model Quick Reference

### estate.property (Property Model)

| Field | Type | Required | Searchable | Notes |
|-------|------|----------|-----------|-------|
| name | Char | ✓ | ✓ | Property name |
| state | Selection | - | ✓ | new, received, accepted, sold, cancel |
| expected_price | Monetary | - | ✓ | Initial asking price |
| best_offer | Monetary | - | ✓ | Computed, stored |
| selling_price | Monetary | - | ✓ | Computed, stored |
| total_area | Integer | - | ✓ | Computed, stored |
| type_id | Many2one | - | ✓ | Link to property type |
| tag_ids | Many2many | - | ✓ | Multiple tags |
| offer_ids | One2many | - | - | Related offers |
| is_manager | Boolean | - | - | Computed for UI control |

**Key Methods**:
- `action_sold()` → Set state to sold
- `action_cancel()` → Set state to cancel
- `_compute_best_offer()` → Calculate highest offer
- `_compute_selling_price()` → Calculate final price

### estate.property.offers (Offer Model)

| Field | Type | Required | Searchable | Notes |
|-------|------|----------|-----------|-------|
| name | Char | - | ✓ | Computed: customer - property |
| price | Monetary | ✓ | ✓ | Offer amount |
| status | Selection | ✓ | ✓ | pending, accepted, refused |
| validity | Integer | ✓ | ✓ | **Computed stored field**: (deadline - creation_date).days |
| deadline | Date | ✓ | ✓ | Regular stored field (editable) |
| creation_date | Date | ✓ | ✓ | When created |
| property_id | Many2one | ✓ | ✓ | Related property |
| partner_id | Many2one | ✓ | ✓ | Customer/buyer |

**Key Methods**:
- `action_accept_offer()` → Accept and refuse others
- `action_refuse_offer()` → Refuse offer
- `create()` → Auto-link to user partner, set initial deadline
- `_compute_validity()` → Auto-compute validity from deadline

**NEW (June 2026)**: Validity is now computed to equal `(deadline - creation_date).days`. This ensures data persistence through page refreshes and server restarts. See `DEADLINE_VALIDITY_FIX.md`.

### estate.property.type (Type Model)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| name | Char | ✓ | Type name (House, Apartment, etc) |

### estate.property.tags (Tags Model)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| name | Char | ✓ | Tag name (Garden, Pool, etc) |
| color | Integer | - | Color code 0-11 |

---

## Common Model Access Patterns

### Create a Property

```python
property = self.env['estate.property'].create({
    'name': 'Beautiful House',
    'expected_price': 500000,
    'bedrooms': 3,
    'living_area': 150,
    'type_id': 1,  # ID of property type
})
```

### Find Properties

```python
# By ID
property = self.env['estate.property'].browse(1)

# By condition
houses = self.env['estate.property'].search([
    ('type_id.name', '=', 'House'),
    ('expected_price', '>', 400000),
])

# All of a type
apartments = self.env['estate.property'].search([
    ('state', '=', 'new'),
    ('type_id.name', '=', 'Apartment'),
], limit=10)
```

### Update Property

```python
# Update single field
property.write({'state': 'sold'})

# Update multiple fields
property.write({
    'state': 'sold',
    'selling_price': 480000,
    'buyer_id': 5,
})

# Update multiple records at once
properties = self.env['estate.property'].search([('state', '=', 'new')])
properties.write({'state': 'received'})
```

### Access Related Records

```python
# Get all offers for property
offers = property.offer_ids

# Filter offers
accepted_offers = property.offer_ids.filtered(
    lambda o: o.status == 'accepted'
)

# Get values from related records
offer_prices = property.offer_ids.mapped('price')  # [500000, 480000, ...]
offer_names = property.offer_ids.mapped('name')

# Access single related record
property_type = property.type_id
type_name = property_type.name

# Access nested related
buyer_name = property.buyer_id.name
buyer_phone = property.buyer_id.phone
```

---

## Security Quick Reference

### User Groups

```
group_property_user
├── Read properties
├── Create own offers
└── See own offers

group_property_sales (implies user group)
├── All user capabilities
├── Accept/refuse offers
├── Create offers on any property
└── Manage all offers

group_property_manager (implies sales group)
├── All sales capabilities
├── Edit property details
├── Manage types/tags
└── Delete properties
```

### Check User Permissions

```python
# Check if user in group
if not self.env.user.has_group('real_estate_ads.group_property_manager'):
    raise AccessError('Only managers can ...')

# Check multiple conditions
if self.env.user.has_group('group_property_sales') or \
   self.env.user.has_group('group_property_manager'):
    # Allow action
```

### Grant User Permission

```
Settings → Users & Companies → Users → Select User
→ Groups tab → Add group
```

---

## View Decorator Quick Reference

### @api.depends

**Purpose**: Recalculate when dependent fields change

**Usage**:
```python
@api.depends('field1', 'field2')
def _compute_something(self):
    for record in self:
        record.computed_field = record.field1 + record.field2
```

**When to use**: Regular computed fields

### @api.depends_context

**Purpose**: Recalculate when context changes (e.g., user changes)

**Usage**:
```python
@api.depends_context('uid')
def _compute_is_manager(self):
    for record in self:
        record.is_manager = self.env.user.has_group('group_property_manager')
```

**When to use**: User-specific computations

### @api.constrains

**Purpose**: Validate before save, raise error if validation fails

**Usage**:
```python
@api.constrains('price')
def _check_price_valid(self):
    for record in self:
        if record.price <= 0:
            raise ValidationError('Price must be > 0')
```

**When to use**: Business rule validation

### @api.onchange

**Purpose**: Update fields in form without saving

**Usage**:
```python
@api.onchange('deadline')
def _onchange_deadline(self):
    for record in self:
        if record.deadline:
            record.validity = # recalculate
```

**When to use**: Real-time UI updates

### @api.model_create_multi

**Purpose**: Override create method for multiple records

**Usage**:
```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        # Pre-process values
    return super().create(vals_list)
```

**When to use**: Auto-populate defaults before create

---

## View Expression Quick Reference

### Invisible Expression

```xml
<!-- Hide field if TRUE -->
<field name="type_id" invisible="not is_manager"/>

<!-- Show only for managers -->
<field name="type_id" invisible="not is_manager"/>

<!-- Hide if condition met -->
<field name="garden_area" invisible="not garden"/>

<!-- Multiple conditions (AND) -->
<field name="x" invisible="(condition1) and (condition2)"/>

<!-- Multiple conditions (OR) -->
<field name="x" invisible="(condition1) or (condition2)"/>
```

### Readonly Expression

```xml
<!-- Read-only for non-managers -->
<field name="name" readonly="not is_manager"/>

<!-- Read-only if status equals 'sold' -->
<field name="price" readonly="status == 'sold'"/>

<!-- Read-only based on multiple conditions -->
<field name="price" readonly="(status == 'sold') or (status == 'cancel')"/>
```

### Button Visibility

```xml
<!-- Show button only to specific group -->
<button name="action_accept_offer"
    string="Accept"
    groups="real_estate_ads.group_property_sales"/>

<!-- Show button AND check conditions -->
<button name="action_accept_offer"
    string="Accept"
    groups="real_estate_ads.group_property_sales"
    invisible="status != 'pending'"/>
```

---

## Common SQL Queries

### Count Offers by Status

```sql
SELECT status, COUNT(*) as count
FROM estate_property_offers
GROUP BY status;
```

### Properties with Most Offers

```sql
SELECT p.name, COUNT(o.id) as offer_count
FROM estate_property p
LEFT JOIN estate_property_offers o ON o.property_id = p.id
GROUP BY p.id
ORDER BY offer_count DESC
LIMIT 10;
```

### Average Price by Property Type

```sql
SELECT pt.name, AVG(p.expected_price) as avg_price
FROM estate_property p
JOIN estate_property_type pt ON pt.id = p.type_id
GROUP BY pt.id;
```

### Offers Expiring Today

```sql
SELECT name, deadline
FROM estate_property_offers
WHERE deadline = CURRENT_DATE
  AND status = 'pending';
```

---

## Debugging Tips

### Enable Debug Mode

```
Settings → Debug Mode → Turn ON
```

### View SQL Queries Generated

```
In Developer Console:
1. Open browser DevTools (F12)
2. Network tab
3. Look for API calls
4. Check parameters and responses
```

### Log Custom Messages

```python
import logging
logger = logging.getLogger(__name__)

def my_method(self):
    logger.info(f"Property: {self.name}")
    logger.warning("Something might be wrong")
    logger.error("Error occurred!")
```

**View logs**:
```
Odoo Server Console Output
or
Settings → Technical → Logs
```

### Print Record Data

```python
def my_method(self):
    print(f"Record ID: {self.id}")
    print(f"Name: {self.name}")
    print(f"Type: {self.type_id.name}")
    print(f"Offers: {len(self.offer_ids)}")
```

### Test Computed Fields

```python
# Reload computed fields
property = self.env['estate.property'].browse(123)
property._compute_total_area()
print(property.total_area)

# Force recalculation
del property.total_area
print(property.total_area)  # Will recalculate
```

---

## Performance Checklist

- [ ] Are you using `store=True` for searchable computed fields?
- [ ] Are you using `mapped()` instead of loops?
- [ ] Are you using `filtered()` instead of list comprehension?
- [ ] Are record rules necessary or can you use ACL?
- [ ] Is any field loading unnecessary related records?
- [ ] Are you paginating large result sets?
- [ ] Is the computed field called too often?

---

## Module Installation Checklist

- [ ] Copy module to addons path
- [ ] `Settings → Apps → Update Apps List`
- [ ] `Apps → Search module → Install`
- [ ] Verify no errors in server logs
- [ ] Create test user and assign groups
- [ ] Test property creation
- [ ] Test offer creation
- [ ] Test offer acceptance workflow
- [ ] Test permissions (user vs manager)
- [ ] Verify fields show/hide correctly

---

## File Edit Locations

### Add New Field to Property

**File**: `models/property.py`
**Location**: After line 51 (before offer_ids)

```python
my_field = fields.Char(string='My Field')
```

### Add New Computed Field

**File**: `models/property.py`
**Location**: After line 58 (after is_manager)

```python
my_computed = fields.Integer(compute='_compute_my_field')

@api.depends('some_field')
def _compute_my_field(self):
    for record in self:
        record.my_computed = # calculation
```

### Add Field to Form View

**File**: `views/property_view.xml`
**Location**: In appropriate group within form

```xml
<field name="my_field"/>
```

### Add New Security Group

**File**: `security/real_estate_ads_groups.xml`
**Location**: After existing groups

```xml
<record id="group_name" model="res.groups">
    <field name="name">Group Name</field>
    <!-- ... rest of group definition -->
</record>
```

---

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `create() missing required argument 'vals'` | Wrong method signature | Use `vals` not `values` |
| `AttributeError: 'NoneType' object` | Accessing field on None | Check record exists: `if record:` |
| `ValidationError: field X not accessible` | Field not in view | Add `<field name="X" invisible="1"/>` |
| `ParseError: while parsing XML` | XML syntax error | Check brackets, quotes match |
| `ParseError: Access Rights Inconsistency` | Using expression not field | Use computed field instead |
| `Database integrity error` | Constraint violation | Check required fields, uniqueness |

---

## External Resources

- **Odoo 19 Documentation**: https://www.odoo.com/documentation/19.0/
- **Odoo Development Tutorials**: https://www.odoo.com/documentation/19.0/developer/tutorials
- **Python Documentation**: https://docs.python.org/3/
- **ORM API Reference**: https://www.odoo.com/documentation/19.0/references/orm

---

## Quick Syntax Reference

### Common ORM Methods

```python
# Search
records = Model.search([('field', 'operator', value)])

# Create
record = Model.create({'field': value})

# Update
record.write({'field': value})

# Delete
record.unlink()

# Browse by ID
record = Model.browse(1)

# Get first/last
first = records[0]
last = records[-1]

# Count
count = len(records)

# Filter
filtered = records.filtered(lambda r: r.field == value)

# Map
values = records.mapped('field_name')

# Sorted
sorted_records = records.sorted('field_name')

# Reverse
reversed_records = records.sorted('field_name', reverse=True)
```

### Common Search Operators

```python
('field', '=', value)        # Equal
('field', '!=', value)       # Not equal
('field', 'in', [v1, v2])    # In list
('field', 'not in', [v1])    # Not in list
('field', '>', value)        # Greater than
('field', '<', value)        # Less than
('field', '>=', value)       # Greater or equal
('field', '<=', value)       # Less or equal
('field', 'like', 'pattern') # Pattern match
('field', 'ilike', 'ipattern') # Case-insensitive
```

### Common Domain Logic

```python
# AND (all must be true)
[('field1', '=', 1), ('field2', '=', 2)]

# OR
['|', ('field1', '=', 1), ('field2', '=', 2)]

# NOT
['!', ('field', '=', value)]

# Complex
['|', ('field1', '=', 1), '&', ('field2', '=', 2), ('field3', '=', 3)]
# Means: field1=1 OR (field2=2 AND field3=3)
```

---

## Recent Fixes & Enhancements

### Deadline & Validity Persistence Fix (June 1, 2026)

**Problem**: Validity would revert to 7 days after page refresh/restart

**Solution**: Reversed field dependencies
- `deadline` → Regular field (source of truth)
- `validity` → Computed stored field

**Impact**: 
- ✅ Cron job extensions now persist
- ✅ No data loss on refresh/restart
- ✅ Automatic calculation

**More Info**: See `DEADLINE_VALIDITY_FIX.md`

**Example**: 
```python
# Cron extends deadline → validity updates automatically
offer.write({'deadline': new_deadline})
# validity = (new_deadline - creation_date).days  # Auto-calculated!
```

---

**Last Updated**: June 1, 2026  
**Odoo Version**: 19.0  
**Module**: real_estate_ads v19.0.1.0.0  
**Document Version**: 2.0

