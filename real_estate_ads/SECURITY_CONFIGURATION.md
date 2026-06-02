# Real Estate Ads Module - Security Configuration Documentation

## Overview
This document outlines the complete security configuration for the `real_estate_ads` module in Odoo 19, implementing three security groups with implied hierarchy and fine-grained role-based access control.

---

## 1. Security Groups Hierarchy

### Group Structure
```
base.group_user
    ↓
group_property_user (Basic property viewer, offer creator)
    ↓
group_property_sales (Sales representative, offer manager)
    ↓
group_property_manager (Full administrator)
```

### Group Definitions (`security/real_estate_ads_groups.xml`)

#### A. Property User Group
- **ID**: `real_estate_ads.group_property_user`
- **Privilege Level**: 10
- **Implied Groups**: `base.group_user`
- **Capabilities**: 
  - View properties (read-only)
  - Create/edit own offers
  - Cannot manage configurations
  - Cannot accept/refuse offers

#### B. Property Sales Group
- **ID**: `real_estate_ads.group_property_sales`
- **Privilege Level**: 20
- **Implied Groups**: `real_estate_ads.group_property_user` (which implies `base.group_user`)
- **Capabilities**:
  - All user capabilities PLUS:
  - Create/edit/delete ALL offers
  - Accept/refuse offers
  - Mark properties as Sold/Cancelled
  - Still cannot edit property details or manage property types/tags

#### C. Property Manager Group
- **ID**: `real_estate_ads.group_property_manager`
- **Privilege Level**: 30
- **Implied Groups**: `real_estate_ads.group_property_sales` (which implies entire hierarchy)
- **Capabilities**:
  - All sales capabilities PLUS:
  - Edit property details (name, description, features, etc.)
  - Manage property types and tags
  - Full system administration for the module

---

## 2. Access Control List (ACL) Configuration

### File: `security/ir.model.access.csv`

#### Property Model Permissions
| Group | Model | Read | Write | Create | Delete |
|-------|-------|------|-------|--------|--------|
| Property User | estate.property | ✓ | ✗ | ✗ | ✗ |
| Property Sales | estate.property | ✓ | ✓ | ✓ | ✗ |
| Property Manager | estate.property | ✓ | ✓ | ✓ | ✓ |

#### Property Type Permissions (Manager-only management)
| Group | Model | Read | Write | Create | Delete |
|-------|-------|------|-------|--------|--------|
| Property User | estate.property.type | ✓ | ✗ | ✗ | ✗ |
| Property Manager | estate.property.type | ✓ | ✓ | ✓ | ✓ |

#### Property Tags Permissions (Manager-only management)
| Group | Model | Read | Write | Create | Delete |
|-------|-------|------|-------|--------|--------|
| Property User | estate.property.tags | ✓ | ✗ | ✗ | ✗ |
| Property Manager | estate.property.tags | ✓ | ✓ | ✓ | ✓ |

#### Property Offers Permissions (All groups can manage via record rules)
| Group | Model | Read | Write | Create | Delete |
|-------|-------|------|-------|--------|--------|
| Property User | estate.property.offers | ✓ | ✓ | ✓ | ✓ |
| Property Sales | estate.property.offers | ✓ | ✓ | ✓ | ✓ |
| Property Manager | estate.property.offers | ✓ | ✓ | ✓ | ✓ |

---

## 3. Record-Level Security Rules

### File: `security/ir_rule_offer.xml`

Record rules enforce data visibility at the database level, restricting which offers each user can see and manage.

#### Rule 1: Property User - Read Own Offers Only
- **Applies To**: `real_estate_ads.group_property_user`
- **Domain**: `[('partner_id', '=', user.partner_id.id)]`
- **Permissions**: Read only (restricted to own offers)
- **Use Case**: Users can only see offers they created

#### Rule 2: Property User - Create Any Offer
- **Applies To**: `real_estate_ads.group_property_user`
- **Domain**: `[(1, '=', 1)]` (unrestricted)
- **Permissions**: Create only
- **Use Case**: Users can create offers for any property

#### Rule 3: Property User - Edit Own Offers
- **Applies To**: `real_estate_ads.group_property_user`
- **Domain**: `[('partner_id', '=', user.partner_id.id)]`
- **Permissions**: Write + Delete (own offers only)
- **Use Case**: Users can modify/delete only their own offers

#### Rule 4: Property Sales/Manager - Full Access to All Offers
- **Applies To**: `real_estate_ads.group_property_sales` (includes managers via hierarchy)
- **Domain**: `[(1, '=', 1)]` (unrestricted)
- **Permissions**: Full CRUD (read, write, create, delete)
- **Use Case**: Sales and managers can see and manage all offers

---

## 4. User Interface Configuration

### File: `views/property_views.xml`

#### Visibility Patterns Used

**Pattern 1: Readonly for Non-Managers**
```xml
readonly="not user_has_groups('real_estate_ads.group_property_manager')"
```
Applied to:
- Property Name
- Postcode, Date Availability
- Description, Bedrooms, Living Area
- Facades, Garage, Garden, Garden Area
- Garden Orientation
- Sales ID, Buyer ID

**Pattern 2: Hidden from Non-Managers**
```xml
invisible="not user_has_groups('real_estate_ads.group_property_manager')"
```
Applied to:
- Property Type field (entire field hidden)
- Property Tags field (entire field hidden)

**Pattern 3: Group-based Button Visibility**
```xml
groups="real_estate_ads.group_property_sales"
```
Applied to:
- "Mark as Sold" button
- "Cancel" button
- "Accept Offer" button (within offers list)
- "Refuse Offer" button (within offers list)

**Pattern 4: Combined Logic Visibility**
```xml
invisible="status != 'pending' or property_state not in ['new', 'received']"
```
Applied to:
- Accept/Refuse buttons (only show when offer is pending AND property in correct state)

---

## 5. Feature Access Matrix

| Feature | User | Sales | Manager |
|---------|------|-------|---------|
| **View Properties** | ✓ Read-only | ✓ Edit | ✓ Full |
| **Edit Property Fields** | ✗ | ✗ | ✓ |
| **Create/Edit Offers** | ✓ Own | ✓ All | ✓ All |
| **Accept/Refuse Offers** | ✗ Hidden | ✓ Visible | ✓ Visible |
| **Mark as Sold/Cancel** | ✗ Hidden | ✓ Visible | ✓ Visible |
| **Manage Property Types** | ✗ Hidden | ✗ Hidden | ✓ Visible |
| **Manage Property Tags** | ✗ Hidden | ✗ Hidden | ✓ Visible |
| **Delete Properties** | ✗ | ✗ | ✓ |
| **View All Offers** | ✗ Own | ✓ All | ✓ All |

---

## 6. Form View Structure

### Header Section (Status Bar)
- "Mark as Sold" button: `groups="real_estate_ads.group_property_sales"`
- "Cancel" button: `groups="real_estate_ads.group_property_sales"`
- Status bar: Visible to all

### Main Group Section
- **Name**: Readonly for all except manager
- **Type**: Invisible for all except manager
- **Tags**: Invisible for all except manager
- **Postcode & Availability**: Readonly for all except manager
- **Price Fields**: Always readonly (computed fields)

### Description Tab
- All fields except Total Area: Readonly for non-managers
- Garden visibility controlled by `invisible="not garden"` condition
- Total Area: Always readonly (computed)

### Offers Tab
- List edit mode: `editable="bottom"` (allows inline editing)
- Offer decorations:
  - `decoration-success="status == 'accepted'"`
  - `decoration-danger="status == 'refused'"`
- Price, Partner, Date, Validity, Deadline: Editable for all groups
- Status: Always readonly
- Accept/Refuse buttons: `groups="real_estate_ads.group_property_sales"` + state logic

### Other Info Tab
- Sales ID & Buyer ID: Readonly for non-managers
- Phone: Always readonly (related field)

---

## 7. Technical Implementation Details

### Odoo 19 Syntax Used
- **Invisible Expressions**: Direct `invisible="..."` attribute (Odoo 17+ syntax)
- **Readonly Expressions**: `readonly="not user_has_groups(...)"` for dynamic control
- **Group References**: Module-prefixed syntax: `real_estate_ads.group_property_*`
- **Record Rules**: `noupdate="0"` flag for development/testing

### Key Technologies
- **Group Hierarchy**: Implicit via `implied_ids` field
- **Record Rules**: Domain-based access control
- **Field-level Security**: Combined with form view attributes
- **Business Logic**: Method-level checks in Python models

---

## 8. Installation & Activation Steps

1. **Install Module**: Deploy the module to your Odoo instance
2. **Load Security Data**: XML files and CSV are loaded automatically
3. **Assign Groups**: Assign users to appropriate groups via Settings > Users & Companies > Users
4. **Test Access**: Log in as user from each group and verify permissions

---

## 9. Related Model Methods with Security Checks

### estate.property Model
- `action_sold()`: Requires `group_property_manager`
- `action_cancel()`: Requires `group_property_manager`

### estate.property.offers Model
- `action_accept_offer()`: Requires `group_property_sales` or `group_property_manager`
- `action_refuse_offer()`: Requires `group_property_sales` or `group_property_manager`

---

## 10. Important Notes

### Design Principles
- ✓ **Principle of Least Privilege**: Users start with minimal access
- ✓ **Clean Hierarchy**: Each group builds on the previous level
- ✓ **UI Consistency**: Fields show/hide based on actual permissions
- ✓ **Backend Enforcement**: Python methods validate access, not just UI
- ✓ **Record Rules Enforce Data**: Even if UI allows, record rules prevent unauthorized access

### Future Enhancements
- Add department-level filtering via record rules
- Implement notification rules per group
- Add audit logging for sensitive actions
- Implement approval workflows before publishing

---

## 11. File Manifest

```
real_estate_ads/
├── security/
│   ├── real_estate_ads_groups.xml       (Group definitions with hierarchy)
│   ├── ir_rule_offer.xml                (Record-level security for offers)
│   └── ir.model.access.csv              (Model-level ACLs)
├── views/
│   ├── property_views.xml               (Form with readonly/invisible controls)
│   ├── property_offer_view.xml          (Offer views - unchanged)
│   ├── property_type_view.xml           (Type views - unchanged)
│   └── property_tag_view.xml            (Tag views - unchanged)
└── __manifest__.py                      (Module manifest)
```

---

## 12. Troubleshooting

### Issue: Users see fields they shouldn't
**Solution**: Clear browser cache and reload module via Settings > Apps > Update Apps List

### Issue: Buttons not appearing for managers
**Solution**: Verify user is actually in manager group (may need to reassign groups in Users settings)

### Issue: Users can still edit fields in list view
**Solution**: List view has separate permissions; use form view for restricted access, or define list-specific view rules

### Issue: Offers not visible to sales users
**Solution**: Check ir_rule_offer.xml rules are loaded; ensure `noupdate="0"` in record rules

---

## Version Information
- **Odoo Version**: 19.0
- **Module Version**: 19.0.1.0.0
- **Last Updated**: 2024
- **Security Model**: Implemented via Groups, ACLs, and Record Rules

---

