# Email Template, Chatter & Report Fix

**Date**: June 11, 2026
**Status**: ✅ Implemented & verified
**Odoo Version**: 19.0
**Module**: real_estate_ads v19.0.1.0.0

This document covers three related changes delivered on June 11, 2026:

1. Fixed the property email template so record data actually renders.
2. Enabled the chatter (messaging + activities) on the property form.
3. Beautified the Property PDF report and fixed a QWeb compile error.

---

## 1. Email Template Data Not Rendering

### Symptom
The "Send Email" action opened the composer and the email sent, but the body
showed **blank values** where property data should appear. The subject line
(`Property Listing: {{ object.name }}`) rendered correctly, which made the bug
confusing.

### Root Cause — two separate problems

**(a) Wrong rendering engine syntax in `body_html`.**
Odoo renders `mail.template` fields with two different engines:

| Field | Engine | Placeholder syntax |
|-------|--------|--------------------|
| `subject`, `email_from`, `partner_to`, `email_to` | `inline_template` | `{{ expression }}` |
| **`body_html`** | **`qweb`** | `t-out`, `t-if`, `t-foreach` |

The original `body_html` used Jinja-style `{{ object.name }}` and `{% if %}`.
QWeb does not interpret those — it left them blank. The `subject` worked only
because it is an `inline_template` field.

**(b) `noupdate="1"` blocked the corrected template from loading.**
The template lives in `data/mail.template.xml` inside `<data noupdate="1">`.
`noupdate="1"` means Odoo **skips the record on module upgrade** if it already
exists, so `-u real_estate_ads` did not overwrite the broken body in the database.

### Fix

**`data/mail.template.xml`** — converted `body_html` to QWeb syntax:

```xml
<!-- BEFORE (Jinja — ignored by QWeb, renders blank) -->
<td>{{ object.name }}</td>
{% if object.description %} ... {% endif %}

<!-- AFTER (QWeb — correct for body_html) -->
<td><t t-out="object.name"/></td>
<t t-if="object.description"> ... </t>
```

`subject`, `email_from`, and `partner_to` keep `{{ }}` — they are
`inline_template` fields and were already correct.

To let the corrected body load during development, `noupdate` was temporarily
set to `"0"`:

```xml
<data noupdate="0">   <!-- temporary, for dev reload -->
```

> ⚠️ **After confirming it works, set `noupdate` back to `"1"`** so end-user
> edits to the template are preserved across future module upgrades.

### Reference (validated against Odoo core)
Odoo's own CRM template `addons/crm/data/mail_template_demo.xml` uses exactly
this pattern: `t-out`/`t-if` in `body_html`, and `{{ }}` only inside
`t-attf-*` attribute strings (`t-attf-src="/logo.png?company={{ object.company_id.id }}"`).
Plain text content always uses `t-out`.

### `action_send_email()` cleanup (`models/property.py`)
Removed redundant / non-functional keys from the composer action:

```python
# Removed: 'views': [(False, 'form')], 'view_id': False  (redundant with view_mode)
#          'default_use_template': bool(template)         (obsolete)
#          'force_email': True                            (not a real context key)
def action_send_email(self):
    self.ensure_one()
    template = self.env.ref('real_estate_ads.email_template_property', raise_if_not_found=False)
    return {
        'type': 'ir.actions.act_window',
        'res_model': 'mail.compose.message',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'default_model': 'estate.property',
            'default_res_ids': self.ids,
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
        },
    }
```

---

## 2. Enable Chatter on the Property Form

### Change
- **Model** (`models/property.py`): added the activity mixin alongside the
  existing thread mixin so the **Activities** scheduler works too:

  ```python
  _inherit = ['mail.thread', 'mail.activity.mixin']
  ```

- **View** (`views/property_view.xml`): replaced the commented-out block with
  the Odoo 19 one-liner chatter, placed right after `</sheet>`:

  ```xml
      </sheet>
      <chatter/>
  </form>
  ```

This adds **Send message / Log note / Activities / Followers** to every
property form. Messages, follower changes, and tracked-field updates are logged
automatically (e.g. `expected_price` already has `tracking=True`).

### Dependency
Requires `mail` in the manifest — already present:
`'depends': ['base', 'mail']`.

---

## 3. Beautify the Property PDF Report

### Changes (`report/report_estate_property.xml`)
Rebuilt `report_estate_property_document` from a flat list of `<p>` lines into a
structured layout using Bootstrap classes that QWeb-PDF supports:

- Title band: property name, postcode, color-coded **status badge**, expected price.
- Three pricing cards: Expected / Best Offer / Selling price (monetary widget
  with the record currency).
- A two-column **details table** (type, availability, bedrooms, areas, garage/garden).
- Garden row only prints when `doc.garden` is set (`t-if`).
- Conditional tag badges and a styled description block.

### QWeb compile error that was fixed
First attempt put a dict literal directly inside a `t-attf-class` interpolation:

```xml
<!-- ❌ RPC_ERROR: "Can not compile expression"
     t-attf uses #{ ... } and stops at the first } — the dict's braces broke it -->
<span t-attf-class="badge #{ {'new':'text-bg-info', ...}.get(doc.state,'...') } fs-6">
```

**Fix** — move the dict into a `t-set` (a real Python expression where braces are
allowed), then interpolate only the simple variable:

```xml
<t t-set="state_class" t-value="{'new': 'text-bg-info', 'received': 'text-bg-warning', 'accepted': 'text-bg-primary', 'sold': 'text-bg-success', 'cancel': 'text-bg-danger'}.get(doc.state, 'text-bg-secondary')"/>
<span t-attf-class="badge #{state_class} fs-6">
    <span t-field="doc.state"/>
</span>
```

> **Rule of thumb:** keep `t-attf-*` / `#{}` expressions to a single
> variable or attribute. Anything containing its own `{}`/`[]` belongs in a
> `t-set t-value`.

The badge colors match the list/kanban mapping:
`new=info`, `received=warning`, `accepted=primary`, `sold=success`, `cancel=danger`.

---

## Files Changed

| File | Change |
|------|--------|
| `data/mail.template.xml` | `body_html` → QWeb (`t-out`/`t-if`); `noupdate="0"` (temp) |
| `models/property.py` | `_inherit` += `mail.activity.mixin`; cleaned `action_send_email()` |
| `views/property_view.xml` | Enabled `<chatter/>` after `</sheet>` |
| `report/report_estate_property.xml` | Restyled document; fixed `t-attf` dict via `t-set` |

---

## How to Deploy & Verify

```bash
# Model changed (activity mixin) + views/report/template reload
python odoo-bin -c odoo.conf -u real_estate_ads --stop-after-init
```

1. **Email**: open a property → **Send Email** → confirm the body table is
   populated with the property data, not blanks.
2. **Chatter**: open the property form → chatter appears below the sheet; verify
   **Send message**, **Log note**, **Activities**, **Followers** all work.
3. **Report**: open a property → **Print → Property Report** → verify the styled
   layout and the color-coded status badge.

> After verifying email, set `data/mail.template.xml` back to `noupdate="1"`.

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Email body still blank | Template not reloaded (`noupdate="1"`) | Set `noupdate="0"`, upgrade, then revert |
| Email body shows literal `{{ ... }}` | Old body still in DB | Re-upgrade; check Settings → Technical → Email → Templates |
| `Can not compile expression` on print | Complex expression inside `t-attf`/`#{}` | Move it to a `t-set t-value` |
| Chatter not visible | `mail` missing from depends, or `<chatter/>` outside `<form>` | Confirm manifest + placement after `</sheet>` |
| PDF styling broken | `wkhtmltopdf` not installed/patched | Install the patched Qt build of wkhtmltopdf |

---

**Status**: 🟢 Complete & Current
**Last Updated**: June 11, 2026
**See also**: `FIX_DOCUMENTATION.md`, `DOCUMENTATION_UPDATES_SUMMARY.md`
