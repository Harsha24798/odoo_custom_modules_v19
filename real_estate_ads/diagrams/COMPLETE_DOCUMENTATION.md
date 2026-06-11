# Real Estate Ads Module - Complete Documentation

> **Module Name**: real_estate_ads  
> **Version**: 19.0.1.0.0  
> **Odoo Version**: 19.0  
> **Author**: Harsha Madushan  
> **License**: LGPL-3  
> **Category**: Administration

---

## Table of Contents

1. [Module Overview](#module-overview)
2. [Module Architecture](#module-architecture)
3. [Data Models](#data-models)
4. [Security System](#security-system)
5. [Views and UI](#views-and-ui)
6. [Business Logic](#business-logic)
7. [Data Flow and Connections](#data-flow-and-connections)
8. [Installation and Setup](#installation-and-setup)
9. [Usage Workflows](#usage-workflows)
10. [Technical Deep Dive](#technical-deep-dive)

---

## Module Overview

### Purpose

The **Real Estate Ads** module is a comprehensive Odoo 19 application designed to manage real estate properties and their offers. It provides:

- **Property Management**: Create, view, and manage real estate properties
- **Offer Management**: Handle buyer offers for properties
- **Property Categorization**: Organize properties by type and tags
- **Role-Based Access Control**: Three-tier security system for different user roles
- **Offer Workflow**: Accept/refuse offers with automatic property state management
- **Business Intelligence**: Track offers, best prices, and property status

### Key Features

✅ Complete property information management  
✅ Multi-level offer tracking with status management  
✅ Automatic price calculations (best offer, selling price)  
✅ Deadline tracking for offers with automatic computation  
✅ Property type and tag management with color coding  
✅ Role-based access control with three security tiers  
✅ Field-level visibility control based on user role  
✅ Comprehensive record-level security rules  
✅ Responsive UI with multiple view types  
✅ Deadline tracking with remaining days display  

---

## Module Architecture

### Directory Structure

```
real_estate_ads/
├── models/
│   ├── __init__.py                    ← Imports all models
│   ├── property.py                    ← Main property model (144 lines)
│   ├── property_offers.py             ← Offer management (191 lines)
│   ├── property_type.py               ← Property type catalog (10 lines)
│   └── property_tags.py               ← Property tags (11 lines)
│
├── views/
│   ├── property_view.xml              ← Property forms, lists, kanban, etc.
│   ├── property_offer_view.xml        ← Offer management views
│   ├── property_type_view.xml         ← Type management views
│   ├── property_tag_view.xml          ← Tag management views
│   └── menu_items.xml                 ← Menu navigation structure
│
├── security/
│   ├── real_estate_ads_groups.xml     ← Role definitions with hierarchy
│   ├── ir.model.access.csv            ← ACL (Access Control List)
│   └── ir_rule_offer.xml              ← Record-level security rules
│
├── data/
│   └── property_type.xml              ← Default property types
│
├── demo/
│   ├── property_type.xml              ← Demo data
│   ├── property.xml                   ← Demo properties
│   └── property_offer.xml             ← Demo offers
│
└── __manifest__.py                    ← Module manifest and configuration

```

### Component Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                     Real Estate Ads Module                   │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
        ┌───────▼────────┐        ┌────────▼──────────┐
        │  Data Layer    │        │  Security Layer   │
        └───────┬────────┘        └────────┬──────────┘
                │                          │
        ┌───────┴────────┐        ┌────────┴──────────┐
        │   4 Models     │        │  3 Security Groups│
        │                │        │  + ACL + Rules    │
        └───────┬────────┘        └────────┬──────────┘
                │                          │
        ┌───────▼────────┐        ┌────────▼──────────┐
        │  View Layer    │        │  Access Control   │
        │  5 View Files  │        │  Field-Level +    │
        │                │        │  Record-Level     │
        └────────────────┘        └───────────────────┘
```

---

## Data Models

### 1. Estate.Property (Main Model)

**File**: `models/property.py`  
**Database Table**: `estate_property`  
**Description**: Core model representing real estate properties

#### Fields

##### Basic Information
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Char(100) | ✓ Yes | Property name/title |
| `description` | Text | ✗ No | Detailed property description |
| `postcode` | Char(10) | ✗ No | Postal/ZIP code |
| `date_availability` | Date | ✗ No | Date property becomes available |

##### Physical Attributes
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `bedrooms` | Integer | - | Number of bedrooms |
| `living_area` | Integer | - | Living area in square meters |
| `facades` | Integer | - | Number of building facades |
| `garage` | Boolean | False | Has garage? |
| `garden` | Boolean | False | Has garden? |
| `garden_area` | Integer | - | Garden area in sq meters (if garden=True) |
| `garden_orientation` | Selection | 'north' | Direction: north, south, east, west |

##### Financial Fields
| Field | Type | Description | Computed |
|-------|------|-------------|----------|
| `expected_price` | Monetary | Initial asking price | ✗ No |
| `best_offer` | Monetary | Highest offer received | ✓ Yes (stored) |
| `selling_price` | Monetary | Final sale price (accepted offer or best) | ✓ Yes (stored) |
| `currency_id` | Many2one | Currency for prices | Defaults to company currency |

##### State and Status
| Field | Type | Options | Description |
|-------|------|---------|-------------|
| `state` | Selection | new, received, accepted, sold, cancel | Current property status |

##### Relationships
| Field | Type | Related To | Description |
|-------|------|-----------|-------------|
| `type_id` | Many2one | estate.property.type | Property type (house, apartment, etc.) |
| `tag_ids` | Many2many | estate.property.tags | Classification tags |
| `sales_id` | Many2one | res.users | Assigned salesperson |
| `buyer_id` | Many2one | res.partner | Buyer/Customer |
| `offer_ids` | One2many | estate.property.offers | All offers for this property |

##### Computed/Related Fields
| Field | Type | Computed | Description |
|-------|------|----------|-------------|
| `total_area` | Integer | ✓ Yes (stored) | living_area + garden_area |
| `phone` | Char | Related | Buyer's phone (linked to buyer_id.phone) |
| `offer_count` | Integer | ✓ Yes | Number of offers received |
| `is_manager` | Boolean | ✓ Yes | Current user is manager? |

#### Key Computations

```python
@api.depends('living_area', 'garden_area')
def _compute_total_area(self):
    """Total area = living area + garden area"""
    # FLOW: User enters living_area or garden_area
    #       → total_area automatically computed
    #       → Stored in database for searching/sorting

@api.depends('offer_ids.price')
def _compute_best_offer(self):
    """Best offer = maximum price from all offers"""
    # FLOW: New offer created
    #       → best_offer recalculated
    #       → Shown in property form

@api.depends('offer_ids.price', 'offer_ids.status')
def _compute_selling_price(self):
    """Selling price = accepted offer price or best offer"""
    # FLOW: Offer accepted
    #       → selling_price = accepted offer price
    #       → OR best_offer if no accepted offer
    #       → Used for financial reporting

@api.depends_context('uid')
def _compute_is_manager(self):
    """is_manager = current user in manager group?"""
    # FLOW: Form loads
    #       → Check user's groups
    #       → is_manager field set to True/False
    #       → Fields/buttons shown/hidden based on this flag
```

#### Key Methods

| Method | Called By | Returns | Purpose |
|--------|-----------|---------|---------|
| `action_sold()` | Button click | - | Mark property as sold (managers only) |
| `action_cancel()` | Button click | - | Cancel property listing (managers only) |
| `action_property_view_offers()` | Button click | ir.actions.act_window | Open offers in new window |

#### Business Logic

**Property State Transitions**:
```
new (initial)
  └─→ received (when first offer created)
      └─→ accepted (when offer accepted)
          └─→ sold (when marked as sold by manager)
  
can also:
new/received/accepted ─→ cancel (manager action)
```

---

### 2. Estate.Property.Offers (Offer Model)

**File**: `models/property_offers.py`  
**Database Table**: `estate_property_offers`  
**Description**: Represents buyer offers for properties

#### Fields

##### Offer Details
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Char | - | Computed: "{customer_name} - {property_name}" |
| `price` | Monetary | ✓ Yes | Offer price |
| `status` | Selection | ✓ Yes | pending, accepted, refused |
| `validity` | Integer | ✓ Yes | **Computed stored field**: (deadline - creation_date).days |
| `creation_date` | Date | ✓ Yes | When offer was created (auto: today) |
| `deadline` | Date | ✓ Yes (stored) | Regular field, editable (initial: creation_date + 7) |

**NEW (June 1, 2026)**: Validity is now a computed stored field that equals `(deadline - creation_date).days`. This ensures validity persists correctly after cron job extensions and server restarts. See `DEADLINE_VALIDITY_FIX.md` for details.

##### Relationships
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `property_id` | Many2one | ✓ Yes | Property being offered on |
| `partner_id` | Many2one | ✓ Yes | Customer making offer (auto-linked to current user's partner) |
| `currency_id` | Related | - | Inherited from property (read-only) |
| `property_state` | Related | - | Current state of the property (for UI logic) |

#### Key Computations

```python
@api.depends('deadline', 'creation_date')
def _compute_validity(self):
    """validity = (deadline - creation_date).days
    
    NEW (June 1, 2026): This ensures validity:
    - Always reflects actual deadline span
    - Persists through page refreshes
    - Persists through server restarts
    - Updates automatically when deadline changes
    """
    # FLOW: Offer created
    #       → deadline set to creation_date + 7 days
    #       → validity auto-computed as (deadline - creation_date).days = 7
    #   
    # OR: Cron extends deadline
    #       → write({'deadline': new_deadline})
    #       → validity auto-recomputed as (new_deadline - creation_date).days
    #       → Example: validity = 32 days (NOT reverted to 7!)

@api.depends('partner_id', 'property_id')
def _compute_name(self):
    """name = "{partner_name} - {property_name}""
    # FLOW: Display name auto-generated for records list
```

#### Key Methods

| Method | Called By | Permission | Purpose |
|--------|-----------|------------|---------|
| `action_accept_offer()` | Button click | Sales/Manager | Accept offer, refuse others, update property state |
| `action_refuse_offer()` | Button click | Sales/Manager | Refuse offer, keep property in received state |
| `create()` | ORM | - | Auto-link offer to current user's partner |

#### Business Logic

**Offer Workflow**:
```
1. Create Offer (all groups)
   └─→ Status: pending
   └─→ Property State changes: new → received
   
2. Accept Offer (sales/manager only)
   └─→ Status: accepted
   └─→ Property State: accepted
   └─→ Auto-refuse all other offers
   └─→ Selling price = this offer's price
   
3. Refuse Offer (sales/manager only)
   └─→ Status: refused
   └─→ Property State: remains received
   └─→ No impact on selling price
   
4. Mark Property as Sold (manager only)
   └─→ Property State: sold
   └─→ Offers become read-only (UI shows buttons hidden)
```

**Constraints**:
- Only ONE offer can be accepted per property
- Offer price must be > 0
- Validity must be > 0 days
- Once accepted, cannot accept another offer without refusing the current one first

---

### 3. Estate.Property.Type (Type Model)

**File**: `models/property_type.py`  
**Database Table**: `estate_property_type`  
**Description**: Property categories/types

#### Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Char(100) | ✓ Yes | Type name (e.g., "House", "Apartment") |

#### Purpose
- **Classification**: Organize properties by type
- **Filtering**: Search/filter properties by type
- **Access Control**: Only managers can create/edit types
- **Linked to**: estate_property.type_id

---

### 4. Estate.Property.Tags (Tags Model)

**File**: `models/property_tags.py`  
**Database Table**: `estate_property_tags`  
**Description**: Property tags for detailed categorization

#### Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | Char(100) | ✓ Yes | Tag name (e.g., "Garden", "Pool") |
| `color` | Integer | default=0 | Color code for UI display (0-11) |

#### Purpose
- **Multi-tag Classification**: Each property can have multiple tags
- **Visual Organization**: Color-coded tags for quick identification
- **Access Control**: Only managers can create/edit tags
- **Related To**: estate_property.tag_ids (Many2many)

---

## Security System

### Security Architecture

The module implements a **three-tier role-based access control** system:

```
┌──────────────────────────────────────────────────────────────┐
│                    User Assignments                          │
├──────────────────────────────────────────────────────────────┤
│ Admin → group_property_manager                               │
│ Sales Team → group_property_sales                            │
│ Viewers → group_property_user                                │
└──────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
        ┌───────▼──────────┐      ┌────────▼──────┐
        │   ACL (Model     │      │  Record Rules │
        │   Level Access)  │      │  (Row Level)  │
        └────────┬─────────┘      └────────┬──────┘
                 │                        │
        ┌────────▼──────────┐      ┌──────▼───────┐
        │ estate.property   │      │ estate.      │
        │   User: R only    │      │ property.    │
        │   Sales: CRU      │      │ offers rules │
        │   Manager: CRUD   │      │              │
        └────────┬──────────┘      └──────┬───────┘
                 │                        │
        ┌────────▼──────────────────────┬┘
        │                               │
        │    UI-Level Access Control    │
        │    (Field visibility/readonly)│
        │                               │
        └───────────────────────────────┘
```

### Security Groups

**File**: `security/real_estate_ads_groups.xml`

#### Group Hierarchy

```
base.group_user (Odoo base)
        │
        └─→ group_property_user (Property User)
            │   └─→ Basic viewers
            │       • Read properties
            │       • Create own offers
            │       • See own offers
            │
            └─→ group_property_sales (Property Sales)
                │   └─→ Sales representatives
                │       • All user capabilities +
                │       • Accept/refuse offers
                │       • Manage all offers
                │       • Mark sold/cancel
                │       • Cannot edit property details
                │
                └─→ group_property_manager (Property Manager)
                    └─→ Administrators
                        • All capabilities
                        • Edit properties
                        • Manage types/tags
                        • Full system control
```

#### Group Definitions

| Group ID | Name | Implies | Permissions |
|----------|------|---------|-------------|
| `real_estate_ads.group_property_user` | Property User | base.group_user | Read properties, Create/edit own offers |
| `real_estate_ads.group_property_sales` | Property Sales | group_property_user | Accept/refuse offers, Mark sold/cancel |
| `real_estate_ads.group_property_manager` | Property Manager | group_property_sales | Full access to all data |

### Access Control List (ACL)

**File**: `security/ir.model.access.csv`

```csv
Model                      User    Sales   Manager
─────────────────────────────────────────────────
estate.property              R      CRU      CRUD
estate.property.type         R      -        CRUD
estate.property.tags         R      -        CRUD
estate.property.offers      CRUD   CRUD     CRUD
```

**Legend**: R=Read, C=Create, U=Update, D=Delete

### Record-Level Rules

**File**: `security/ir_rule_offer.xml`

Record rules enforce **row-level security** by restricting which records users can see:

#### Rule 1: Property User - Read Own Offers
```
Domain: [('partner_id', '=', user.partner_id.id)]
Effect: Users only see offers they created
Applies to: group_property_user
```

#### Rule 2: Property User - Create Any Offer
```
Domain: [(1, '=', 1)]  # No restriction
Effect: Users can create offers on any property
Applies to: group_property_user
```

#### Rule 3: Property User - Edit Own Offers
```
Domain: [('partner_id', '=', user.partner_id.id)]
Effect: Users can edit/delete only their own offers
Applies to: group_property_user
```

#### Rule 4: Sales/Manager - Full Access
```
Domain: [(1, '=', 1)]  # No restriction
Effect: See and manage all offers
Applies to: group_property_sales (includes managers)
```

### Field-Level Visibility

**Implemented in View**: `views/property_view.xml`

The `is_manager` computed field controls field visibility:

```python
readonly="not is_manager"     # Read-only unless manager
invisible="not is_manager"    # Hidden unless manager
```

**Controlled Fields**:
- Property Name, Type, Tags (invisible)
- Postcode, Date, Description (readonly)
- Bedrooms, Area, Garden info (readonly)
- Sales ID, Buyer ID (readonly)

---

## Views and UI

### View Files Structure

#### 1. Property Views (`views/property_view.xml`)

**Form View** (for detailed property data)
- Header: Status bar + action buttons
- Main group: Name, Type, Tags, Postcode, Prices
- Notebook tabs:
  - Description: Property details
  - Offers: Inline editable offer list
  - Other Info: Sales person, buyer

**List View** (for browsing properties)
- Columns: Name, Offer count, Postcode, Availability
- Optional columns: Description, Price, Status

**Search View** (for filtering)
- Search fields: Name, Postcode, Type
- Filters: By state (New, Received, Accepted, Sold, Canceled)
- Price ranges: 0-250k, 250k-500k, etc.

**Kanban View** (visual card layout)
- Cards grouped by state
- Shows: Name, Type, Postcode, Area, Beds

**Pivot View** (analytics)
- Expected price by type and state

**Graph View** (charting)
- Property analysis over time

**Calendar View** (date-based)
- Properties by availability date

#### 2. Offer Views (`views/property_offer_view.xml`)

- Form view for individual offers
- List view with decoration (green=accepted, red=refused)
- Search view with status filters

#### 3. Type Views (`views/property_type_view.xml`)

- Simple list/form for property types
- Name field only
- Managers can CRUD

#### 4. Tag Views (`views/property_tag_view.xml`)

- List/form for property tags
- Name and color selection
- Managers can CRUD

#### 5. Menu Items (`views/menu_items.xml`)

```
Real Estate Ads (root menu)
├── Properties
│   ├── Properties (list view action)
│   ├── Offers (list view action)
│   └── ─── (separator)
│   ├── Property Types (management)
│   └── Property Tags (management)
└── Dashboard (optional)
```

### View Features by User Role

#### Property User
- **Can See**: List view of all properties, own offers
- **Cannot See**: Type/Tags fields, accept/refuse buttons
- **Fields**: Read-only (except creating new offers)

#### Property Sales
- **Can See**: All properties, all offers, accept/refuse buttons
- **Cannot See**: Type/Tags fields
- **Fields**: Read-only (except offers and sold/cancel state)

#### Property Manager
- **Can See**: Everything
- **Can Edit**: All fields including Type/Tags
- **Full Access**: Complete CRUD on all data

---

## Business Logic

### Offer Acceptance Workflow

```
User Action: Click "Accept" button on offer

┌─────────────────────────────────────────┐
│ 1. Validation Phase                     │
├─────────────────────────────────────────┤
│ • Check user is in sales/manager group  │
│ • Check property doesn't have accepted  │
│   offer already                         │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ 2. Update Phase                         │
├─────────────────────────────────────────┤
│ • Set offer status = 'accepted'         │
│ • Set property state = 'accepted'       │
│ • Set selling_price = this offer price  │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ 3. Auto-Cleanup Phase                   │
├─────────────────────────────────────────┤
│ • Find all other offers on this prop    │
│ • Set all to status = 'refused'         │
│ • Update best_offer computation         │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ ✓ Offer Accepted                        │
│ • Customer sees property as accepted    │
│ • Other buyers see their offers refused │
│ • Sales team can now mark as sold       │
└─────────────────────────────────────────┘
```

### Offer Creation Workflow

```
User Action: Create new offer on property

┌─────────────────────────────────────────┐
│ 1. Pre-Creation Phase                   │
├─────────────────────────────────────────┤
│ • If no partner_id provided             │
│ • Auto-link to current user's partner   │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ 2. Validation Phase                     │
├─────────────────────────────────────────┤
│ • price > 0 (constraint check)          │
│ • validity > 0 (constraint check)       │
│ • property_id exists (required)         │
│ • partner_id exists (required)          │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ 3. Auto-Computation Phase               │
├─────────────────────────────────────────┤
│ • name = "{partner} - {property}"       │
│ • status = 'pending'                    │
│ • creation_date = today                 │
│ • deadline = today + validity days      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ 4. Property Update Phase                │
├─────────────────────────────────────────┤
│ • IF property.state == 'new'            │
│   → change to 'received'                │
│ • Recompute property.best_offer         │
│ • Recompute property.offer_count        │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ ✓ Offer Created                         │
│ • Visible in property's offer tab       │
│ • Visible to authorized users           │
│ • Awaiting sales/manager response       │
└─────────────────────────────────────────┘
```

### Computed Fields Recalculation

```
┌────────────────────────────────────────┐
│ Event: User edits garden_area          │
└────────┬───────────────────────────────┘
         │
         ├─→ _compute_total_area()
         │   └─→ total_area = living_area + garden_area
         │       ✓ Instant refresh in form
         │
         └─→ Record saved to database
             └─→ Stored computed fields updated
                 ✓ Persisted for searching

┌────────────────────────────────────────┐
│ Event: New offer created                │
└────────┬───────────────────────────────┘
         │
         ├─→ _compute_best_offer()
         │   └─→ best_offer = max(all_offer_prices)
         │       ✓ Instant in form
         │
         ├─→ _compute_offer_count()
         │   └─→ offer_count = len(offer_ids)
         │       ✓ Instant in form
         │
         └─→ _compute_selling_price()
             └─→ selling_price = accepted_offer or best_offer
                 ✓ Instant in form

┌────────────────────────────────────────┐
│ Event: Property form loads              │
└────────┬───────────────────────────────┘
         │
         └─→ _compute_is_manager()
             └─→ is_manager = user.has_group(
                     'group_property_manager'
                 )
                 ✓ Determines field visibility
                 ✓ Determines button visibility
```

---

## Data Flow and Connections

### Connection Diagram

```
┌─────────────────────────────────────────────────────────┐
│         Odoo System (base.group_user)                   │
│              (res.users, res.partner)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ depends on
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────────────┐  ┌────────▼──────────────┐
│  res.users             │  │  res.partner          │
│  (User accounts)       │  │  (Contacts/Customers) │
│                        │  │                       │
│ • name                 │  │ • name                │
│ • partner_id ─────────┼──┼─→ • phone             │
│ • groups_id            │  │ • email               │
└───────┬────────────────┘  └┬──────────────────────┘
        │                    │
        │ has_group()        │
        │                    │
┌───────▼────────────────────▼──────────────────────┐
│                                                   │
│     Estate.Property Model                         │
│     (Main real estate entities)                   │
│                                                   │
│  Key Fields:                                      │
│  • name, postcode, date_availability             │
│  • bedrooms, living_area, facades                │
│  • garage, garden, garden_area                   │
│  • expected_price, best_offer, selling_price    │
│  • state (new→received→accepted→sold)           │
│  • type_id (FK → estate.property.type)           │
│  • tag_ids (M2M → estate.property.tags)          │
│  • sales_id (FK → res.users)                     │
│  • buyer_id (FK → res.partner)                   │
│  • offer_ids (O2M → estate.property.offers)      │
│  • is_manager (computed, depends on user groups) │
│                                                   │
└───┬───────────┬──────────────┬────────────────────┘
    │           │              │
    │ one-to-many              │
    │ offers     │              │
    │            │              │
    │    ┌───────▼──────────┐   │
    │    │                  │   │
    ▼    ▼                  │   │
┌────────────────────┐      │   │
│ Estate.Property    │      │   │
│ .Offers            │      │   │
│                    │      │   │
│ • name (computed)  │      │   │
│ • price (monetary) │      │   │
│ • status           │      │   │
│ • validity         │      │   │
│ • creation_date    │      │   │
│ • deadline         │      │   │
│ • partner_id (FK)  │      │   │
│ • property_state   │      │   │
│  (related field)   │      │   │
│                    │      │   │
└────────────────────┘      │   │
         │                  │   │
         │ many-to-one      │   │
         │ back to          │   │
         │ property         │   │
         │                  │   │
         └──────────────────┼───┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
    ┌───────▼──────────────┐      ┌────────▼──────────────┐
    │ Estate.Property      │      │ Estate.Property       │
    │ .Type                │      │ .Tags                 │
    │                      │      │                       │
    │ • name (required)    │      │ • name (required)     │
    │                      │      │ • color               │
    │ Used for:            │      │                       │
    │ Classification,      │      │ Used for:             │
    │ Filtering            │      │ Multi-tag grouping    │
    │                      │      │                       │
    └──────────────────────┘      └───────────────────────┘
```

### Data Relationships

#### 1. Property ← Offers (One-to-Many)

```
property_id = 1
    ├─→ offer_id = 1 ($250,000, pending)
    ├─→ offer_id = 2 ($260,000, pending)
    ├─→ offer_id = 3 ($255,000, accepted) ← best_offer
    └─→ offer_id = 4 ($240,000, refused)

Results:
• best_offer = 260,000 (before acceptance)
• after offer 3 accepted:
  - best_offer = 260,000
  - selling_price = 255,000 (accepted)
  - offer_ids[2] and [4] marked 'refused'
```

#### 2. Property ← Type (Many-to-One)

```
property.type_id = 5 (House)
property_type.id = 5
property_type.name = "House"

Result: Property categorized as House type
```

#### 3. Property ← Tags (Many-to-Many)

```
property.tag_ids = [1, 3, 5]
├─→ tag 1 = "Garden" (color: blue)
├─→ tag 3 = "Pool" (color: green)
└─→ tag 5 = "Garage" (color: yellow)

Result: Property can be searched/filtered by all tags
```

#### 4. Offer ← Buyer (Many-to-One)

```
offer.partner_id = 10 (Customer Name)
offer.buyer_id ← links to: res.partner(id=10)
offer.phone ← related field from: res.partner(10).phone

Result: Offer linked to specific customer
```

---

## Installation and Setup

### Prerequisites

- Odoo 19.0 installed and running
- Base module installed
- Administrator access to Odoo

### Installation Steps

#### Step 1: Place Module in Addons Path

```bash
# Copy the real_estate_ads folder to your Odoo addons directory
cp -r real_estate_ads /path/to/odoo/addons/
```

#### Step 2: Update Module List

In Odoo:
```
Settings → Apps → Update Apps List
```

#### Step 3: Install Module

```
Apps → Search "Real Estate Ads" → Install
```

The system will automatically:
- Create all model tables
- Load security groups
- Apply ACLs
- Load all views
- Create demo data (if enabled)

#### Step 4: Configure Security Groups

```
Settings → Users & Companies → Users
→ Select user
→ Groups tab
→ Assign appropriate group:
   • group_property_user (basic user)
   • group_property_sales (sales rep)
   • group_property_manager (admin)
```

#### Step 5: Load Demo Data (Optional)

If demo data wasn't loaded automatically:
```
Settings → Technical → Data Files
→ Choose demo files:
   • property_tag.xml
   • property.xml
   • property_offer.xml
→ Load
```

---

## Usage Workflows

### Workflow 1: Property Manager Creates Property

```
1. Navigate: Real Estate Ads → Properties
2. Click: Create
3. Enter:
   • Name: "Beautiful House in Downtown"
   • Type: House
   • Postcode: 12345
   • Expected Price: $500,000
   • Bedrooms: 3
   • Living Area: 150 sqm
   • Garden: Yes
   • Garden Area: 500 sqm
   • Description: Full details...
4. Save → Property Status: NEW
5. Click: Save & Close
6. View menu shows new property
```

### Workflow 2: Customer Creates Offer

```
1. Navigate: Real Estate Ads → Properties → View list
2. Click: Property name (open form)
3. Scroll: Offers tab
4. Click: Add offer
5. Enter:
   • Price: $480,000
   • Validity: 7 days
6. Save → Offer automatically linked to current user
         → Property state changes: NEW → RECEIVED
         → Best offer = $480,000
         → Deadline = today + 7 days
```

### Workflow 3: Sales Person Accepts Offer

```
1. Navigate: Real Estate Ads → Properties
2. Open: Property with pending offers
3. Scroll: Offers tab
4. Find: Desired offer
5. Click: "Accept" button
   
System automatically:
   • Sets offer status = "accepted"
   • Sets property state = "accepted"
   • Refuses all other offers
   • Updates selling_price = accepted price
   • Notifies other buyers (via refused status)

6. Now property ready for manager to mark as sold
```

### Workflow 4: Manager Marks Property as Sold

```
1. Open: Accepted property
2. Header: See "Mark as Sold" button (only for managers)
3. Click: "Mark as Sold"
4. Confirm: Yes
5. Property state changes: ACCEPTED → SOLD
6. All buttons hidden (system locks down further changes)
7. Property removed from active sales
```

### Workflow 5: Manager Cancels Property

```
1. Open: Any property in NEW/RECEIVED/ACCEPTED state
2. Header: See "Cancel" button (only for managers)
3. Click: "Cancel"
4. Confirm: Yes
5. Property state changes: [any] → CANCELED
6. All editing disabled
7. Property removed from active listing
```

---

## Technical Deep Dive

### API Decorators and Methods

#### `@api.depends(*fields)`

```python
@api.depends('living_area', 'garden_area')
def _compute_total_area(self):
    """
    Decorator tells Odoo: when living_area OR garden_area changes,
    recalculate total_area
    """
    for record in self:
        record.total_area = (record.living_area or 0) + (record.garden_area or 0)
```

**How it works**:
1. Field watched: living_area, garden_area
2. Trigger: User changes either field
3. Action: _compute_total_area() called
4. Result: total_area updated instantly in form
5. Save: When record saved, computed value stored

#### `@api.depends_context(*context_keys)`

```python
@api.depends_context('uid')
def _compute_is_manager(self):
    """
    Decorator tells Odoo: when user context (uid) changes,
    recompute is_manager
    """
    for record in self:
        record.is_manager = self.env.user.has_group(
            'real_estate_ads.group_property_manager'
        )
```

**How it works**:
1. Watches: Current user ID (uid in context)
2. Trigger: User switches or logs in
3. Action: _compute_is_manager() called
4. Result: Field reflects whether user is manager
5. Impact: UI shows/hides fields based on value

#### `@api.constrains(*fields)`

```python
@api.constrains('price')
def _check_price_positive(self):
    """
    Decorator tells Odoo: when 'price' field is saved,
    validate it meets constraint
    """
    for record in self:
        if record.price <= 0:
            raise ValidationError('Offer price must be greater than 0.')
```

**How it works**:
1. Trigger: User tries to save record
2. Check: price > 0?
3. If False: Raise error, block save
4. If True: Allow save to proceed
5. User sees: Error message in UI

#### `@api.onchange(*fields)`

```python
@api.onchange('deadline', 'creation_date')
def _onchange_deadline(self):
    """
    Decorator tells Odoo: when user changes deadline or creation_date,
    trigger this method BEFORE saving
    """
    for record in self:
        if record.deadline:
            record.validity = record._compute_validity_from_deadline(
                record.creation_date, 
                record.deadline
            )
```

**How it works**:
1. Trigger: User edits deadline field
2. Action: _onchange_deadline() called
3. Result: validity field updated INSTANTLY
4. Saves: NOT YET (user sees change in form)
5. UI: Shows updated value without saving

#### `@api.model_create_multi`

```python
@api.model_create_multi
def create(self, vals_list):
    """
    Decorator tells Odoo: this is a create override that handles multiple records
    """
    for vals in vals_list:
        if not vals.get('partner_id') and self.env.user.partner_id:
            vals['partner_id'] = self.env.user.partner_id.id
    return super().create(vals_list)
```

**How it works**:
1. Trigger: User creates new offer(s)
2. Action: If partner_id not provided
3. Auto-fill: partner_id = current user's partner
4. Result: Offer linked to user automatically
5. Saves: Proceed with normal create

### Computed Fields vs Regular Fields

```
Regular Field (Char, Integer, etc.)
├─ Stored in database
├─ User enters value
└─ Static until user changes

Computed Field (no store=True)
├─ NOT stored in database
├─ Calculated on-the-fly
├─ Recalculated when dependencies change
├─ Lost when record closed and reopened
└─ Use: Instant UI feedback

Computed Stored Field (store=True)
├─ Calculated once
├─ Result stored in database
├─ Searchable and sortable
├─ Persists across sessions
└─ Use: best_offer, total_area, selling_price
```

### Related Fields

```python
phone = fields.Char(related='buyer_id.phone', readonly=True)
```

**How it works**:
1. Points to: buyer_id.phone field
2. Follows chain: property.buyer_id → res.partner(id).phone
3. Displays: Buyer's phone in property form
4. Readonly: Cannot edit here (edit via partner)
5. Use: Convenience for users (avoid scrolling)

### Many2One Relations

```python
type_id = fields.Many2one('estate.property.type', string='Property Type')
```

**How it works**:
```
estate_property.type_id = [FK to estate_property_type.id]

Database:
│ property_id │ name          │ type_id │
├─────────────┼───────────────┼─────────┤
│ 1           │ House ABC     │ 5       │  ← Points to Type #5
│ 2           │ Apartment XYZ │ 8       │  ← Points to Type #8

property_type:
│ id │ name       │
├────┼────────────┤
│ 5  │ House      │
│ 8  │ Apartment  │
```

### One2Many Relations

```python
offer_ids = fields.One2many('estate.property.offers', 'property_id', string='Offers')
```

**How it works**:
```
property_id = 1
    Has multiple offers (inverse side)

estate_property_offers:
├─ offer_id = 101, property_id = 1, price = $500k
├─ offer_id = 102, property_id = 1, price = $520k
└─ offer_id = 103, property_id = 1, price = $480k

When property form opens:
    offer_ids = [101, 102, 103]
    All shown in offer_ids tab
```

### Many2Many Relations

```python
tag_ids = fields.Many2many('estate.property.tags', string='Property Tags')
```

**How it works**:
```
property_id = 1: garden, pool, garage
property_id = 2: garage, modern
property_id = 3: garden, modern

Junction table (created automatically):
│ property_id │ tag_id │
├─────────────┼────────┤
│ 1           │ garden │
│ 1           │ pool   │
│ 1           │ garage │
│ 2           │ garage │
│ 2           │ modern │
│ 3           │ garden │
│ 3           │ modern │
```

### Security Rules Examples

#### Example 1: User Can Only See Own Offers

```python
# In ir_rule_offer.xml
domain_force = [('partner_id', '=', user.partner_id.id)]

Interpretation:
├─ For each user
├─ Show offers where partner_id = current user's partner_id
└─ Result: User sees ONLY their own offers
```

#### Example 2: No Domain Restriction

```python
# In ir_rule_offer.xml
domain_force = [(1, '=', 1)]  # Always true

Interpretation:
├─ (1, '=', 1) is always true
├─ No filtering applied
└─ Result: See ALL records (permission per group)
```

### Field Visibility Logic

**In View Attributes**:

```xml
<!-- If is_manager = True -->
readonly="not is_manager"
    → readonly="not True"
    → readonly="False"  ← EDITABLE

<!-- If is_manager = False -->
readonly="not is_manager"
    → readonly="not False"
    → readonly="True"   ← READ-ONLY

<!-- Example 2: Hidden field -->
<!--If is_manager = True -->
invisible="not is_manager"
    → invisible="not True"
    → invisible="False"  ← VISIBLE

<!-- If is_manager = False -->
invisible="not is_manager"
    → invisible="not False"
    → invisible="True"   ← HIDDEN
```

---

## Performance Considerations

### Computed Fields Performance

```
Unoptimized:
@api.depends('offer_ids')
def _compute_offer_count(self):
    for record in self:
        record.offer_count = len(record.offer_ids)
        # For each record, loads ALL related offers from DB
        # O(n) complexity

Performance Tip:
• Use store=True for search/sort operations
• Use depends properly to minimize recalculations
• Avoid loading large related records unnecessarily
```

### Record Rules Performance

```
Without rules: query 1000 properties instantly
With rules: Odoo adds WHERE clause to every query
    SELECT * FROM estate_property
    WHERE property_id IN (
        SELECT id FROM estate_property WHERE ...rules applied...
    )

Performance Impact:
├─ Minimal for <10,000 records
├─ Noticeable for >100,000 records
└─ Optimize rules as business grows
```

---

## Troubleshooting

### Issue: Fields Show Read-Only for Managers

**Cause**: is_manager field returning False incorrectly

**Solution**:
```
1. Go to: Settings → Users → User profile
2. Check: Groups tab → Verify manager group assigned
3. Clear cache: Settings → Technical → Clear Cache
4. Refresh: Browser Hard Refresh (Ctrl+Shift+R)
```

### Issue: Offer Creation Changes Property State

**Expected Behavior**: Property state changes NEW → RECEIVED when first offer created

**If Not Happening**:
```
1. Check: onchange method firing
2. Verify: property_state field in offer model
3. Solution: Save offer to trigger DB update
```

### Issue: Type/Tags Fields Not Visible to Managers

**Cause**: View not loaded correctly

**Solution**:
```
1. Clear: browser cache + restart Odoo
2. Go to: Settings → Technical → Views → estate.property.form
3. Search: invisible="not is_manager"
4. Verify: helper field <field name="is_manager" invisible="1"/>
```

---

## Conclusion

The **Real Estate Ads** module is a complete, production-ready Odoo application for managing real estate properties and offers. It demonstrates:

✅ Clean architecture with 4 linked models  
✅ Three-tier role-based security  
✅ Computed fields and data relationships  
✅ Business logic workflows  
✅ Multi-view UI components  
✅ Advanced Odoo features (decorators, constraints, etc.)  

This documentation provides everything needed to understand, maintain, and extend the module.

---

**Document Version**: 1.0  
**Last Updated**: May 21, 2026  
**Module Version**: 19.0.1.0.0  
**Odoo Version**: 19.0

