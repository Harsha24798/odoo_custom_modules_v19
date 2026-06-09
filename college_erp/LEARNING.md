# College ERP — Complete Technical Learning Material
> Odoo 19 | Built from scratch — every concept explained with real code from this module.

---

## Table of Contents
1. [Module Structure](#1-module-structure)
2. [__manifest__.py](#2-__manifest__py)
3. [__init__.py — Python Package Wiring](#3-__initpy--python-package-wiring)
4. [Models — The Database Layer](#4-models--the-database-layer)
5. [Fields — All Types Used](#5-fields--all-types-used)
6. [Model Attributes](#6-model-attributes)
7. [Database Constraints](#7-database-constraints)
8. [CRUD Methods — create & write](#8-crud-methods--create--write)
9. [Computed Fields & @api.depends](#9-computed-fields--apidepends)
10. [ir.sequence — Auto Numbering](#10-irsequence--auto-numbering)
11. [TransientModel — Wizards](#11-transientmodel--wizards)
12. [Security — Groups, Privileges & Access Rights](#12-security--groups-privileges--access-rights)
13. [Views — XML UI Layer](#13-views--xml-ui-layer)
14. [Menus & Window Actions](#14-menus--window-actions)
15. [Client Actions — Rainbow Effect](#15-client-actions--rainbow-effect)
16. [Sending Email via mail.mail](#16-sending-email-via-mailmail)
17. [Context Passing Between Views](#17-context-passing-between-views)
18. [Key API Decorators — Quick Reference](#18-key-api-decorators--quick-reference)
19. [Common Mistakes & How We Fixed Them](#19-common-mistakes--how-we-fixed-them)

---

## 1. Module Structure

```
college_erp/
├── __init__.py                        # Marks directory as Python package
├── __manifest__.py                    # Module metadata & file registry
├── data/
│   └── ir_sequence_data.xml           # Auto-number sequence definition
├── models/
│   ├── __init__.py                    # Imports all model files
│   ├── college_student.py             # Main student model
│   └── student_email.py              # Email wizard (TransientModel)
├── security/
│   ├── college_erp_security.xml       # Groups & privileges
│   └── ir.model.access.csv           # CRUD permissions per group
├── static/
│   └── description/
│       └── icon.png                   # App icon shown in Odoo home
└── views/
    ├── college_student_views.xml      # List, Form, Action for students
    ├── student_email_wizard_views.xml # Email wizard popup form
    └── college_erp_menus_views.xml    # Menu tree
```

**Rule:** Odoo loads files in the exact order listed in `__manifest__.py → data`. Security must come before views because views may reference groups.

---

## 2. `__manifest__.py`

```python
{
    'name': 'College Erp',
    'version': '19.0.1.0.0',   # format: <odoo_version>.<major>.<minor>.<patch>
    'author': 'Harsha Madushan',
    'category': 'Education',
    'website': 'https://www.harshamadusha.com',
    'summary': 'College ERP System',
    'description': """...""",
    'license': 'LGPL-3',
    'sequence': 2,              # position in the app list (lower = higher up)

    'depends': ['base'],        # modules this module requires
    'data': [                   # XML/CSV files loaded in order
        'security/college_erp_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/college_student_views.xml',
        'views/student_email_wizard_views.xml',
        'views/college_erp_menus_views.xml',
    ],

    'application': True,        # shows in the app switcher
    'installable': True,
    'auto_install': False,
}
```

### Key fields explained

| Field | Purpose |
|---|---|
| `depends` | Other modules that must be installed first. `base` is always the minimum. |
| `data` | Files loaded when installing/upgrading. Order matters — later files can reference records from earlier files. |
| `application` | `True` gives it an icon in the home screen. |
| `version` | First segment must match Odoo major version (`19.0`). |

---

## 3. `__init__.py` — Python Package Wiring

**Root `__init__.py`:**
```python
from . import models
```
Tells Python the `models/` folder is a sub-package to load.

**`models/__init__.py`:**
```python
from . import college_student
from . import student_email
```
Each model file must be imported here. If you add a new model file and forget this, Odoo will never see the class — no table will be created.

---

## 4. Models — The Database Layer

### `models.Model` — Persistent (has a database table)
```python
class CollegeStudent(models.Model):
    _name = 'college.student'        # table name: college_student
    _description = 'College Student Details'
    _rec_name = 'admission_no'
```
Every class that inherits `models.Model` gets its own PostgreSQL table. The `_name` (dots replaced with underscores) is the table name.

### `models.TransientModel` — Temporary (wizard)
```python
class StudentEmail(models.TransientModel):
    _name = 'student.email'
    _description = 'Send Email to Student'
```
- Same as `Model` but records are **auto-deleted** after a configurable time (default 1 hour).
- Used for wizards, popups, one-shot forms — anything that doesn't need permanent storage.
- Has a real DB table (`student_email`) but Odoo's garbage collector cleans it.

### Comparison

| | `models.Model` | `models.TransientModel` |
|---|---|---|
| DB table | Yes, permanent | Yes, temporary |
| Auto-cleanup | No | Yes (~1 hour) |
| Use case | Business data | Wizards, dialogs |

---

## 5. Fields — All Types Used

### `fields.Char` — short text
```python
admission_no = fields.Char(
    string='Admission Number',
    required=True,      # NOT NULL in DB + mandatory in UI
    copy=False,         # not duplicated when record is copied
    readonly=True,      # cannot be edited in UI
    default='New',      # initial value before save
    index=True,         # creates DB index — speeds up search
)
```

### `fields.Date` — date only (no time)
```python
admission_date = fields.Date(string='Admission Date', required=True)
birth_day = fields.Date(string='Birth Day')
```
Stored as `DATE` in PostgreSQL. Use `fields.Datetime` for timestamp.

### `fields.Integer`
```python
age = fields.Integer(string='Age', compute='_compute_age')
```

### `fields.Text` — long text (multiline)
```python
communication_address = fields.Text(string='Communication Address', required=True)
```

### `fields.Boolean`
```python
same_as_communication = fields.Boolean('Same as Communication', default=True)
```

### `fields.Image`
```python
image_1920 = fields.Image(string='Student Image')
```
`image_1920` is the Odoo standard field name for full-size images. Odoo automatically generates `image_128` and `image_256` thumbnails from it.

### `fields.Html`
```python
body = fields.Html(string='Body', required=True)
```
Stored as HTML string. Renders with the rich-text editor in the UI.

### `fields.Many2one` — foreign key (N→1)
```python
state_id = fields.Many2one(
    'res.country.state',
    'Fed. State',
    domain="[('country_id', '=?', country_id)]"  # filters dropdown options
)
country_id = fields.Many2one('res.country')
student_id = fields.Many2one('college.student', string='Student', readonly=True)
```
- Creates a FK column `<field_name>_id` in the DB.
- `domain` filters what appears in the dropdown. `'=?'` means "filter only if the right side is set".

### `fields.Char` with `related` — proxy field
```python
country_code = fields.Char(related='country_id.code', string='Country Code')
```
- Reads from a related record — no extra column in DB.
- Automatically read-only unless `readonly=False` is set explicitly.
- Updates when the linked record updates.

### Computed field
```python
age = fields.Integer(string='Age', compute='_compute_age')
```
- Not stored in DB by default (`store=False`).
- Recalculated every time the record is read.
- Add `store=True` to persist it in DB (useful for search/group-by).

---

## 6. Model Attributes

```python
class CollegeStudent(models.Model):
    _name = 'college.student'       # unique technical name — DO NOT change after deploy
    _description = 'College Student Details'  # human label shown in UI
    _rec_name = 'admission_no'      # field shown in Many2one dropdowns and breadcrumbs
```

### `_rec_name`
By default Odoo looks for a field called `name`. Since our model has no `name` field, without `_rec_name` it would display `college.student,2` (model name + id). Setting `_rec_name = 'admission_no'` shows `STD0001` instead.

### `_order`
Not used here but important to know:
```python
_order = 'admission_date desc, admission_no'  # default sort order for list views
```

---

## 7. Database Constraints

### Old way (`_sql_constraints`) — still works, not preferred in v19
```python
_sql_constraints = [
    ('admission_no_unique', 'UNIQUE(admission_no)', 'Admission number must be unique.'),
]
```

### New way (`models.Constraint`) — Odoo 17+/19 standard
```python
_admission_no_unique = models.Constraint(
    'UNIQUE(admission_no)',
    'Admission number must be unique.',
)
```
- Defined as a **class attribute** — cleaner, more readable.
- Translates to the same `ALTER TABLE ... ADD CONSTRAINT` SQL underneath.
- The error message is shown to the user when the constraint is violated.
- Enforced at the **database level** — catches violations even from raw SQL or imports.

### Why DB constraints beat Python validation
Python `search()` checks have a race condition: two simultaneous requests can both pass the check, then both insert, creating a duplicate. A DB `UNIQUE` constraint is atomic — the second insert will fail at the DB level regardless.

---

## 8. CRUD Methods — `create` & `write`

### `create` — `@api.model_create_multi`
```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if vals.get('admission_no', 'New') == 'New':
            vals['admission_no'] = (
                self.env['ir.sequence'].next_by_code('college.student.admission.no') or 'New'
            )
    return super().create(vals_list)
```

**`@api.model_create_multi` vs `@api.model`:**

| | `@api.model` (old) | `@api.model_create_multi` (v17+/19) |
|---|---|---|
| Signature | `def create(self, vals)` | `def create(self, vals_list)` |
| Input | single dict | list of dicts |
| Batch support | No | Yes |
| Performance | 1 SQL per record | 1 SQL for all records |

Always use `@api.model_create_multi` in Odoo 17+/19. If you override `create`, process `vals_list` in a `for` loop.

**`self.env['ir.sequence'].next_by_code('...')`** — fetches the next value from a named sequence (see section 10).

### `write` — update
```python
def write(self, vals):
    if 'admission_no' in vals and self.env['college.student'].search_count(
        [('admission_no', '=', vals['admission_no']), ('id', 'not in', self.ids)],
        limit=1,
    ):
        raise ValidationError('Admission number must be unique.')
    return super().write(vals)
```

- `vals` is a dict of only the **changed** fields, not all fields.
- `self` can be a **recordset** (multiple records) — `self.ids` gives all their IDs.
- `('id', 'not in', self.ids)` excludes the records being updated from the duplicate check.
- `search_count(..., limit=1)` stops after finding one match — faster than loading the full recordset.
- Always call `super().write(vals)` at the end; skipping it means nothing actually saves.

### `search_count` vs `search`

```python
# Less efficient — loads ORM objects just to check existence
duplicate = self.env['college.student'].search([...], limit=1)
if duplicate:
    ...

# More efficient — issues SELECT COUNT, no record hydration
if self.env['college.student'].search_count([...], limit=1):
    ...
```

### `ensure_one()`
```python
def action_send_email(self):
    self.ensure_one()   # raises if self has 0 or 2+ records
```
Guards methods that only make sense on a single record (e.g. opening a form for *this* student).

---

## 9. Computed Fields & `@api.depends`

```python
@api.depends('birth_day')
def _compute_age(self):
    today = date.today()          # called ONCE outside the loop — not N times
    for record in self:
        if record.birth_day:
            record.age = (
                today.year - record.birth_day.year
                - ((today.month, today.day) < (record.birth_day.month, record.birth_day.day))
            )
        else:
            record.age = 0
```

**`@api.depends('birth_day')`** — Odoo re-runs this method whenever `birth_day` changes. Without this decorator, `age` would never update.

**Correct age formula:**
The tuple comparison `(today.month, today.day) < (birth_day.month, birth_day.day)` returns `True` (= 1) if the birthday has not yet occurred this year. Subtracting 1 corrects the year difference.

| Birthday | Today | Simple year diff | Correction | Correct age |
|---|---|---|---|---|
| Dec 1, 1990 | Jun 9, 2026 | 36 | −1 (not yet) | **35** |
| Mar 1, 1990 | Jun 9, 2026 | 36 | −0 (passed) | **36** |

**`store=True` on computed fields:**
```python
age = fields.Integer(compute='_compute_age', store=True)
```
- Without `store=True`: recalculated on every read, never in DB.
- With `store=True`: saved to DB, can be filtered/sorted in list views, triggers recompute on dependency change.

---

## 10. `ir.sequence` — Auto Numbering

### Data file: `data/ir_sequence_data.xml`
```xml
<record id="college_student_admission_no_sequence" model="ir.sequence">
    <field name="name">College Student Admission Number</field>
    <field name="code">college.student.admission.no</field>  <!-- lookup key -->
    <field name="prefix">STD</field>                         <!-- text before number -->
    <field name="padding">4</field>                          <!-- zero-pad to 4 digits -->
    <field name="number_increment">1</field>                 <!-- step -->
    <field name="use_date_range">False</field>
</record>
```
Generates: `STD0001`, `STD0002`, `STD0003` ...

### Python usage
```python
self.env['ir.sequence'].next_by_code('college.student.admission.no')
```
- Looks up the sequence with `code = 'college.student.admission.no'`.
- Atomically increments the counter and returns the formatted string.
- Thread-safe — no two calls return the same value.

### `use_date_range`
When `True`, the sequence resets per year/month/day. Useful for invoice numbers (`INV/2026/00001`).

### Updating an existing sequence
If the module is already installed, changing the XML won't update the DB record. Go to:
**Settings → Technical → Sequences** and edit prefix/padding there manually.

---

## 11. TransientModel — Wizards

```python
class StudentEmail(models.TransientModel):
    _name = 'student.email'
    _description = 'Send Email to Student'

    student_id = fields.Many2one('college.student', readonly=True)
    email_to   = fields.Char(string='To', readonly=True)
    subject    = fields.Char(string='Subject', required=True)
    body       = fields.Html(string='Body', required=True)
```

### `default_get` — pre-filling fields from context
```python
@api.model
def default_get(self, fields_list):
    res = super().default_get(fields_list)
    student_id = self.env.context.get('default_student_id')
    if student_id:
        student = self.env['college.student'].browse(student_id)
        res['student_id'] = student.id
        res['email_to'] = student.email
    return res
```
- `default_get` is called before the wizard form opens.
- `self.env.context` is a dict of values passed when the action was triggered.
- `default_<field_name>` in context is the Odoo convention for pre-filling a field.
- `browse(id)` fetches a record by primary key without a search query.

### Sending the email
```python
def action_send(self):
    self.ensure_one()
    self.env['mail.mail'].create({
        'subject': self.subject,
        'email_to': self.email_to,
        'body_html': self.body,
    }).send()
    return {'type': 'ir.actions.act_window_close'}
```
- `mail.mail` is Odoo's outgoing email model (requires an outgoing mail server configured in Settings).
- `.send()` dispatches immediately.
- Returning `{'type': 'ir.actions.act_window_close'}` closes the wizard popup.

---

## 12. Security — Groups, Privileges & Access Rights

### Step 1 — Module category (`college_erp_security.xml`)
```xml
<record id="module_category_college_erp_cat" model="ir.module.category">
    <field name="name">College ERP</field>
</record>
```
Groups this module's security groups together in Settings → Users.

### Step 2 — Privilege (Odoo 19 feature)
```xml
<record id="res_groups_privilege_college_erp" model="res.groups.privilege">
    <field name="name">College ERP</field>
    <field name="category_id" ref="module_category_college_erp_cat"/>
</record>
```
`res.groups.privilege` is new in Odoo 17+/19. It groups related security groups into a single dropdown in the user form, replacing the old radio-button selector.

### Step 3 — Groups with inheritance
```xml
<!-- Teacher: basic user -->
<record id="group_college_erp_teacher" model="res.groups">
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
</record>

<!-- Staff inherits Teacher -->
<record id="group_college_erp_staff" model="res.groups">
    <field name="implied_ids" eval="[(4, ref('group_college_erp_teacher'))]"/>
</record>

<!-- Principal inherits both Teacher and Staff -->
<record id="group_college_erp_principal" model="res.groups">
    <field name="implied_ids" eval="[(4, ref('group_college_erp_teacher')),
                                     (4, ref('group_college_erp_staff'))]"/>
</record>
```

**`implied_ids` — group inheritance:**
A user in `Staff` automatically gets all permissions of `Teacher`. A `Principal` gets all permissions of both. This avoids duplicating access rules.

**`eval="[(4, ref(...))]"`** — Odoo ORM command:

| Command | Meaning |
|---|---|
| `(4, id)` | Link existing record (add to Many2many) |
| `(3, id)` | Unlink record |
| `(5,)` | Remove all links |
| `(0, 0, vals)` | Create and link new record |

### Step 4 — Access rights (`ir.model.access.csv`)
```
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_college_student,access.college.student,college_erp.model_college_student,base.group_user,1,0,0,0
access_college_teacher,...,group_college_erp_teacher,1,1,1,0
access_college_staff,...,group_college_erp_staff,1,1,1,0
access_college_principal,...,group_college_erp_principal,1,1,1,1
```

| Column | Meaning |
|---|---|
| `model_id:id` | `<module>.model_<model_name_with_underscores>` |
| `perm_read` | SELECT |
| `perm_write` | UPDATE |
| `perm_create` | INSERT |
| `perm_unlink` | DELETE |

**Permission matrix for this module:**

| Group | Read | Write | Create | Delete |
|---|:---:|:---:|:---:|:---:|
| All users | ✓ | | | |
| Teacher | ✓ | ✓ | ✓ | |
| Staff | ✓ | ✓ | ✓ | |
| Principal | ✓ | ✓ | ✓ | ✓ |

---

## 13. Views — XML UI Layer

### List View
```xml
<record id="college_student_list_view" model="ir.ui.view">
    <field name="name">college.student.view.list</field>
    <field name="model">college.student</field>
    <field name="arch" type="xml">
        <list string="College Student List">
            <field name="admission_no"/>
            <field name="email"/>
            <field name="mother_name" optional="hide"/>  <!-- hidden by default, user can show -->
        </list>
    </field>
</record>
```

### Form View
```xml
<form string="College Student Form" create="false">  <!-- disables the New button -->
    <header>
        <button name="action_send_email" type="object" string="Send Email" class="oe_highlight"/>
    </header>
    <sheet>
        <field name="image_1920" widget="image" class="oe_avatar"/>
        <group>
            <group>...</group>
            <group>...</group>
        </group>
        <notebook>
            <page string="Permanent Address" invisible="same_as_communication">
                ...
            </page>
        </notebook>
    </sheet>
</form>
```

**Key form concepts:**

| Element | Purpose |
|---|---|
| `<header>` | Top bar — status buttons and action buttons |
| `<sheet>` | Main form body |
| `<group><group>` | Two-column layout |
| `<notebook><page>` | Tabbed sections |
| `class="oe_avatar"` | Positions image as a round avatar |
| `class="oe_highlight"` | Blue primary button style |
| `optional="hide"` | Column hidden by default in list, user can toggle |
| `invisible="same_as_communication"` | Hide when boolean field is True |
| `create="false"` | Removes the New button from the form |

### Button types

| `type` | What it does |
|---|---|
| `type="object"` | Calls a Python method on the model |
| `type="action"` | Triggers a window/client action by XML id |
| `special="cancel"` | Closes the wizard without saving (wizards only) |

### Widget examples
```xml
<field name="same_as_communication" widget="boolean_toggle"/>  <!-- toggle switch -->
<field name="image_1920" widget="image"/>                       <!-- image preview -->
<field name="body" widget="html"/>                              <!-- rich text editor -->
```

### Wizard View
```xml
<form string="Send Email">
    <group>
        <field name="student_id"/>
        <field name="email_to" readonly="1"/>
        <field name="subject"/>
    </group>
    <group>
        <field name="body" widget="html" nolabel="1"/>
    </group>
    <footer>
        <button name="action_send" type="object" string="Send" class="btn-primary"/>
        <button string="Cancel" class="btn-secondary" special="cancel"/>
    </footer>
</form>
```
Wizards use `<footer>` instead of `<header>` for action buttons.

---

## 14. Menus & Window Actions

### Window Action — what opens when a menu is clicked
```xml
<record id="action_college_erp" model="ir.actions.act_window">
    <field name="name">College ERP</field>
    <field name="res_model">college.student</field>
    <field name="view_mode">list,form,kanban</field>
</record>
```

### Menu tree
```xml
<!-- Level 1: Root (app icon) -->
<menuitem id="college_erp_menu_root" name="College ERP"
    sequence="1" web_icon="college_erp,static/description/icon.png"/>

<!-- Level 2: Section -->
<menuitem id="college_erp_menu_dashboard" name="Dashboard"
    parent="college_erp_menu_root"/>

<!-- Level 3: Item with action -->
<menuitem id="college_erp_menu_student" name="Student"
    parent="college_erp_menu_dashboard"
    action="action_college_erp" sequence="1"/>

<!-- Restricted to principals only -->
<menuitem id="college_erp_menu_teacher" name="Teacher"
    parent="college_erp_menu_dashboard"
    action="action_college_erp" sequence="2"
    groups="group_college_erp_principal"/>
```

`groups="..."` on a menuitem hides it from users who don't belong to that group.

---

## 15. Client Actions — Rainbow Effect

```python
def action_rainbow_effect(self):
    return {
        'effect': {
            'fadeout': 'slow',
            'message': 'This is the rainbow effect',
            'img_url': '/web/static/img/smile.svg',
            'type': 'rainbow_man',
        }
    }
```
Returning a dict with `'effect'` key from a button method triggers a client-side animation. No page reload needed. Commonly used on milestone actions (first invoice paid, etc.).

---

## 16. Sending Email via `mail.mail`

```python
self.env['mail.mail'].create({
    'subject': self.subject,
    'email_to': self.email_to,   # comma-separated string for multiple recipients
    'body_html': self.body,
}).send()
```

**`mail.mail` vs `mail.message`:**

| | `mail.mail` | `mail.message` |
|---|---|---|
| Purpose | Outgoing SMTP email | Internal chatter message |
| Sends to external email | Yes | No (unless email_from set) |
| Requires mail server | Yes | No |
| Stored permanently | Cleaned after send | Yes |

**Prerequisites:** Settings → Technical → Outgoing Mail Servers must have a configured SMTP server.

---

## 17. Context Passing Between Views

```python
# In college_student.py
def action_send_email(self):
    self.ensure_one()
    return {
        'name': 'Send Email',
        'type': 'ir.actions.act_window',
        'res_model': 'student.email',
        'view_mode': 'form',
        'target': 'new',                              # opens as popup dialog
        'context': {'default_student_id': self.id},  # passed to the wizard
    }
```

```python
# In student_email.py
@api.model
def default_get(self, fields_list):
    res = super().default_get(fields_list)
    student_id = self.env.context.get('default_student_id')  # read from context
    if student_id:
        student = self.env['college.student'].browse(student_id)
        res['student_id'] = student.id
        res['email_to'] = student.email
    return res
```

**Convention:** `default_<field_name>` in context automatically sets that field's default value. `default_get` is where you intercept this to compute related defaults (like fetching the email from the student record).

**`target` options:**

| `target` | Behaviour |
|---|---|
| `'current'` (default) | Opens in the main content area |
| `'new'` | Opens as a modal popup dialog |
| `'fullscreen'` | Opens full-screen overlay |
| `'inline'` | Opens inline in the current form |

---

## 18. Key API Decorators — Quick Reference

| Decorator | `self` is | Use for |
|---|---|---|
| `@api.model` | Empty recordset of the model | Class-level ops: `default_get`, `create` (old way) |
| `@api.model_create_multi` | Empty recordset | `create` override — receives `vals_list` |
| `@api.depends('field1', 'field2')` | Recordset | Computed field methods |
| `@api.onchange('field1')` | Single record (form only) | React to field change in UI (not saved until form save) |
| `@api.constrains('field1')` | Recordset | Python validation (raise ValidationError) |
| *(no decorator)* | Recordset | Regular instance methods: `write`, `unlink`, custom actions |

---

## 19. Common Mistakes & How We Fixed Them

### 1. Using `request.env` in a model method
```python
# WRONG
existing = request.env['college.student'].search([])

# CORRECT
existing = self.env['college.student'].search([])
```
`request` is an HTTP object available only in controllers. Inside models always use `self.env`.

### 2. Empty method body (syntax error)
```python
# WRONG — Python SyntaxError
def write(self, vals):

def action_rainbow_effect(self):
    ...

# CORRECT
def write(self, vals):
    return super().write(vals)
```

### 3. Wrong age calculation
```python
# WRONG — off by 1 for people whose birthday hasn't happened yet this year
record.age = today.year - record.birth_day.year

# CORRECT
record.age = (
    today.year - record.birth_day.year
    - ((today.month, today.day) < (record.birth_day.month, record.birth_day.day))
)
```

### 4. `date.today()` inside loop
```python
# WRONG — calls date.today() for every record
for record in self:
    record.age = date.today().year - ...

# CORRECT — call once before the loop
today = date.today()
for record in self:
    record.age = today.year - ...
```

### 5. `search()` for existence check
```python
# LESS EFFICIENT — hydrates ORM objects
if self.env['college.student'].search([...], limit=1):

# MORE EFFICIENT — only a COUNT query
if self.env['college.student'].search_count([...], limit=1):
```

### 6. Missing `_rec_name`
Without `_rec_name`, a model with no `name` field displays as `college.student,2` in Many2one dropdowns. Set `_rec_name` to any meaningful Char field.

### 7. `@api.model` on `create` in Odoo 19
```python
# OLD (Odoo 16 and below)
@api.model
def create(self, vals):
    return super().create(vals)

# CORRECT for Odoo 17+/19
@api.model_create_multi
def create(self, vals_list):
    return super().create(vals_list)
```

---

*End of learning material — covers every file and concept in the `college_erp` module as built.*
