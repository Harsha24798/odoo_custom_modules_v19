# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Assume Odoo is installed at `C:\Users\harsh\OneDrive\Desktop\Odoo\V19` and a config file exists (e.g., `odoo.conf`). Adjust paths as needed.

**Install / upgrade the module:**
```
python odoo-bin -c odoo.conf -u real_estate_ads --stop-after-init
```

**Run all module tests:**
```
python odoo-bin -c odoo.conf --test-enable -u real_estate_ads --stop-after-init
```

**Run a specific test class or method:**
```
python odoo-bin -c odoo.conf --test-enable --test-tags /real_estate_ads:TestPropertyModel -u real_estate_ads --stop-after-init
python odoo-bin -c odoo.conf --test-enable --test-tags /real_estate_ads:TestPropertyModel.test_total_area_computation -u real_estate_ads --stop-after-init
```

**Run with demo data:**
Add `--load-language=en_US` and ensure `demo = True` in `odoo.conf`, or pass `--without-demo=False`.

## Module Architecture

**Technical name:** `real_estate_ads`  
**Odoo version:** 19.0  
**Depends:** `base`, `mail` (`mail` is required for the chatter, the `mail.template`, and tracked fields)

### Models and relationships

```
estate.property          (models/property.py)
  ├── Many2one → estate.property.type    (type_id)
  ├── Many2one → res.users               (sales_id)
  ├── Many2one → res.partner             (buyer_id)
  ├── Many2many → estate.property.tags  (tag_ids)
  └── One2many → estate.property.offers (offer_ids)

estate.property.offers   (models/property_offers.py)
  ├── Many2one → estate.property        (property_id)
  └── Many2one → res.partner            (partner_id)

estate.property.type     (models/property_type.py)   — simple name-only model
estate.property.tags     (models/property_tags.py)   — name + color integer
```

### Property state machine

`estate.property.state` transitions:
- `new` → `received` (when an offer is created — **must be set manually in `create()`, not automatic today**)
- `received` → `accepted` (via `action_accept_offer()` on `estate.property.offers`)
- `accepted` → `sold` (via `action_sold()` on the property — manager only)
- any → `cancel` (via `action_cancel()` — manager only)

Refusing all offers does **not** revert state back to `new`; it stays `received`.

### Security model (3-tier RBAC)

Groups defined in `security/real_estate_ads_groups.xml` with strict implication chain:

| Group | XML ID | Inherits |
|---|---|---|
| Property User | `group_property_user` | `base.group_user` |
| Property Sales | `group_property_sales` | `group_property_user` |
| Property Manager | `group_property_manager` | `group_property_sales` |

Because of `implied_ids`, a manager also satisfies any `has_group('...group_property_sales')` check. Always check the **lowest** group that should have access.

Record rule in `security/ir_rule_offer.xml`: Users (`group_property_user`) can only see/edit their **own** offers (`user_id = uid`). Sales and managers see all offers via a `[(1,'=',1)]` rule.

### UI access control pattern

The form view uses a computed boolean `is_manager` (with `@api.depends_context('uid')`) instead of inline `groups=` attributes on individual fields. This allows `readonly="not is_manager"` expressions in XML. The field is rendered invisible in the form:
```xml
<field name="is_manager" invisible="1"/>
```

Buttons in the form header (`action_sold`, `action_cancel`) use `groups="real_estate_ads.group_property_sales"` — but the Python methods currently enforce **manager-only** access. This mismatch means Sales users see the buttons but get `AccessError`. Fix by aligning the Python check to match the button visibility.

### Messaging: chatter, email template & report

`estate.property` inherits `['mail.thread', 'mail.activity.mixin']`. The form
view enables the chatter with a single `<chatter/>` tag placed **after
`</sheet>`** (Odoo 18/19 syntax — no `oe_chatter` div, no separate
`message_ids`/`activity_ids` fields). `expected_price` has `tracking=True`, so
its changes are logged in the chatter.

**Email template** (`data/mail.template.xml`): the `body_html` field is rendered
by the **QWeb** engine, so it must use `t-out` / `t-if` / `t-foreach` — **not**
`{{ }}` or `{% %}` (those only work in `inline_template` fields like `subject`,
`email_from`, `partner_to`). `{{ }}` is valid inside `t-attf-*` attribute
strings only. The template record sits in a `noupdate` data block: keep it at
`"1"` for production (preserves user edits) and flip to `"0"` only when you need
an upgrade to overwrite the body during development.

`action_send_email()` on the property opens `mail.compose.message` in `comment`
mode with `default_template_id` and `default_res_ids`.

**PDF report** (`report/report_estate_property.xml`): `report_estate_property`
calls `report_estate_property_document`. Keep `t-attf-*` / `#{}` interpolations
to a single variable — put any expression containing `{}`/`[]` (e.g. a dict
`.get()` for the status badge class) into a `t-set t-value` first, or QWeb
fails to compile.

See `EMAIL_CHATTER_REPORT_FIX.md` for the full write-up (June 11, 2026).

### Offer deadline / validity round-trip

`deadline` is a stored computed field with an inverse:
- `_compute_deadline`: `deadline = creation_date + validity days`
- `_inverse_deadline`: editing deadline back-calculates `validity`
- `_onchange_deadline`: keeps the UI responsive before save

Minimum validity enforced at 1 day in both compute and inverse paths.

### Known issues to be aware of

1. **`tests/__init__.py` is missing** — Odoo won't discover tests without it. Create an empty file at `tests/__init__.py`.
2. **`expected_price` is hardcoded `readonly="1"`** in the form — managers cannot edit it via the UI.
3. **`widget="statinfo"`** on `offer_count` in the list view is a form-view-only widget; remove or replace it.
4. **`widget="char_emojis"`** on the `name` field is not a standard Odoo widget and may cause JS errors.
5. **`data/estet.property_type.csv`** — dead file (typo in name, not in manifest). Safe to delete.
6. **Test assertion bug** in `test_offer_acceptance`: asserts `property.state == 'received'` after offer creation, but offer creation doesn't change property state today.
7. **Test group ref bug** in `test_user_cannot_access_manager_features`: references `'module.group_property_user'` — should be `'real_estate_ads.group_property_user'`.

### Data files load order (manifest)

Security files must load before views (groups referenced in view `groups=` attributes). Current order in `__manifest__.py`:
1. `security/real_estate_ads_groups.xml` → defines groups
2. `security/ir_rule_offer.xml` → defines record rules (references groups)
3. `security/ir.model.access.csv` → grants model-level permissions
4. View XML files
5. `data/property_type.xml` (seed data, `noupdate="1"`)
