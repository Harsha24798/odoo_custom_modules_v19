# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

**Install / upgrade the module (run from Odoo root):**
```bash
python odoo-bin -d <database> -u college_erp --stop-after-init
```

**Run a single test:**
```bash
python odoo-bin -d <database> --test-enable --stop-after-init -u college_erp
```

**Restart Odoo after Python changes** (views-only changes just need a browser refresh in debug mode):
```bash
python odoo-bin -d <database>
```

## Architecture

This is a single Odoo 19 module (`college_erp`) that depends on `base` and `sale`.

### Models

| Model | Type | Table | Purpose |
|---|---|---|---|
| `college.student` | `models.Model` | `college_student` | Core student records with auto-numbered admission IDs |
| `student.email` | `models.TransientModel` | `student_email` | Wizard for composing and sending email to a student |
| `sale.order` (extended) | `_inherit` | `sale_order` | Adds a `student_id` Many2one column to the existing sale order table |

### Key patterns

**Auto-numbering:** `admission_no` defaults to `'New'` and is replaced on `create` via `ir.sequence` code `college.student.admission.no` → `STD0001`, `STD0002` …

**Wizard → email flow:**
1. `CollegeStudent.action_send_email` opens `student.email` as a popup (`target: 'new'`), passing `{'default_student_id': self.id}` in context.
2. `StudentEmail.default_get` reads that context key to pre-fill `student_id`, `email_to` (from student), and `email_from` (`self.env.user.email`).
3. `StudentEmail.action_send` creates and sends a `mail.mail` record, then returns `ir.actions.act_window_close`.

**Model inheritance (`inheritance_models.py`):** Uses `_inherit = 'sale.order'` (extension type — no new table) to add `student_id`. The matching view patch is in `views/sale_order_inherit_views.xml`.

**Security hierarchy:** Principal ⊃ Staff ⊃ Teacher ⊃ base user. Implemented via `implied_ids` on `res.groups`. Only Principal has `perm_unlink`.

### Odoo 19-specific conventions used here

- Use `@api.model_create_multi` (not `@api.model`) on `create`; the argument is `vals_list` (a list of dicts).
- Use `models.Constraint(...)` class attribute for DB-level unique constraints (not `_sql_constraints`).
- Override `_compute_display_name` (not the deprecated `name_get`) when customising how a record appears in breadcrumbs and Many2one dropdowns.
- `res.groups.privilege` (new in v17+) groups security groups into a single dropdown in user profiles.

### File loading order matters

`__manifest__.py → data` must list security files before views (views reference group XML ids). The current order is:
1. `security/college_erp_security.xml`
2. `security/ir.model.access.csv`
3. `data/ir_sequence_data.xml`
4. Views

### Sequence updates

After the module is installed, editing the XML sequence record does **not** update the database. Change prefix/padding via **Settings → Technical → Sequences** in the Odoo UI, or drop and reinstall the module.
