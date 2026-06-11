from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date


class TestCollegeStudent(TransactionCase):

    def _make_student(self, **overrides):
        vals = {
            'admission_date': date.today(),
            'first_name': 'John',
            'last_name': 'Doe',
            'father_name': 'Richard Doe',
            'mother_name': 'Jane Doe',
            'communication_address': '123 Main St',
        }
        vals.update(overrides)
        return self.env['college.student'].create(vals)

    # --- Admission number ---

    def test_create_generates_admission_no(self):
        student = self._make_student()
        self.assertTrue(student.admission_no.startswith('STD'))
        self.assertNotEqual(student.admission_no, 'New')

    def test_create_multiple_students_get_unique_numbers(self):
        s1 = self._make_student()
        s2 = self._make_student(first_name='Jane')
        self.assertNotEqual(s1.admission_no, s2.admission_no)

    def test_create_with_explicit_admission_no_is_preserved(self):
        student = self._make_student(admission_no='MANUAL001')
        self.assertEqual(student.admission_no, 'MANUAL001')

    def test_bulk_create_generates_sequential_numbers(self):
        students = self.env['college.student'].create([
            {
                'admission_date': date.today(),
                'first_name': 'Alice',
                'last_name': 'A',
                'father_name': 'FA',
                'mother_name': 'MA',
                'communication_address': 'Addr A',
            },
            {
                'admission_date': date.today(),
                'first_name': 'Bob',
                'last_name': 'B',
                'father_name': 'FB',
                'mother_name': 'MB',
                'communication_address': 'Addr B',
            },
        ])
        self.assertEqual(len(students), 2)
        self.assertNotEqual(students[0].admission_no, students[1].admission_no)
        self.assertTrue(all(s.admission_no.startswith('STD') for s in students))

    def test_write_duplicate_admission_no_raises_validation_error(self):
        s1 = self._make_student()
        s2 = self._make_student(first_name='Jane')
        with self.assertRaises(ValidationError):
            s2.write({'admission_no': s1.admission_no})

    def test_write_other_fields_does_not_alter_admission_no(self):
        student = self._make_student()
        original_no = student.admission_no
        student.write({'first_name': 'Updated'})
        self.assertEqual(student.admission_no, original_no)

    # --- Age computation ---

    def test_compute_age_birthday_already_passed(self):
        # Jan 1 is always before or equal to today, so birthday has occurred
        birth = date(date.today().year - 25, 1, 1)
        student = self._make_student(birth_day=birth)
        self.assertEqual(student.age, 25)

    def test_compute_age_birthday_not_yet_reached(self):
        today = date.today()
        if today.month == 12 and today.day == 31:
            self.skipTest('Cannot test future birthday on Dec 31')
        # Dec 31 of 25 years ago has not arrived yet (for any date before Dec 31)
        birth = date(today.year - 25, 12, 31)
        student = self._make_student(birth_day=birth)
        self.assertEqual(student.age, 24)

    def test_compute_age_no_birthday_returns_zero(self):
        student = self._make_student()
        self.assertEqual(student.age, 0)

    def test_compute_age_updates_when_birthday_changes(self):
        student = self._make_student(birth_day=date(date.today().year - 20, 1, 1))
        self.assertEqual(student.age, 20)
        student.birth_day = date(date.today().year - 30, 1, 1)
        self.assertEqual(student.age, 30)

    # --- Display name ---

    def test_display_name_format_is_admission_no_and_first_name(self):
        student = self._make_student()
        self.assertEqual(student.display_name, f'[{student.admission_no}] John')

    def test_display_name_reflects_first_name_changes(self):
        student = self._make_student()
        student.first_name = 'Alice'
        self.assertIn('Alice', student.display_name)

    # --- Required fields ---

    def test_missing_first_name_raises(self):
        with self.assertRaises(Exception):
            self.env['college.student'].create({
                'admission_date': date.today(),
                'last_name': 'Doe',
                'father_name': 'Father',
                'mother_name': 'Mother',
                'communication_address': 'Address',
            })

    def test_missing_admission_date_raises(self):
        with self.assertRaises(Exception):
            self.env['college.student'].create({
                'first_name': 'John',
                'last_name': 'Doe',
                'father_name': 'Father',
                'mother_name': 'Mother',
                'communication_address': 'Address',
            })

    # --- Button actions ---

    def test_action_send_email_opens_student_email_wizard(self):
        student = self._make_student()
        action = student.action_send_email()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'student.email')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['view_mode'], 'form')

    def test_action_send_email_passes_student_id_in_context(self):
        student = self._make_student()
        action = student.action_send_email()
        self.assertEqual(action['context']['default_student_id'], student.id)

    def test_action_rainbow_effect_returns_rainbow_man_type(self):
        student = self._make_student()
        result = student.action_rainbow_effect()
        self.assertEqual(result['effect']['type'], 'rainbow_man')
        self.assertIn('message', result['effect'])
