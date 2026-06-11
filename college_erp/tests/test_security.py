from odoo.tests import TransactionCase
from odoo.exceptions import AccessError
from datetime import date


class TestCollegeStudentSecurity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.teacher_group = self.env.ref('college_erp.group_college_erp_teacher')
        self.staff_group = self.env.ref('college_erp.group_college_erp_staff')
        self.principal_group = self.env.ref('college_erp.group_college_erp_principal')

        self.teacher_user = self.env['res.users'].create({
            'name': 'Test Teacher',
            'login': 'test_teacher@college.test',
            'email': 'test_teacher@college.test',
            'groups_id': [(4, self.teacher_group.id)],
        })
        self.staff_user = self.env['res.users'].create({
            'name': 'Test Staff',
            'login': 'test_staff@college.test',
            'email': 'test_staff@college.test',
            'groups_id': [(4, self.staff_group.id)],
        })
        self.principal_user = self.env['res.users'].create({
            'name': 'Test Principal',
            'login': 'test_principal@college.test',
            'email': 'test_principal@college.test',
            'groups_id': [(4, self.principal_group.id)],
        })

    def _make_student(self):
        return self.env['college.student'].create({
            'admission_date': date.today(),
            'first_name': 'Test',
            'last_name': 'Student',
            'father_name': 'Test Father',
            'mother_name': 'Test Mother',
            'communication_address': '1 Test St',
        })

    # --- Read access ---

    def test_teacher_can_read_student(self):
        student = self._make_student()
        first_name = student.with_user(self.teacher_user).first_name
        self.assertEqual(first_name, 'Test')

    def test_staff_can_read_student(self):
        student = self._make_student()
        first_name = student.with_user(self.staff_user).first_name
        self.assertEqual(first_name, 'Test')

    def test_principal_can_read_student(self):
        student = self._make_student()
        first_name = student.with_user(self.principal_user).first_name
        self.assertEqual(first_name, 'Test')

    # --- Create access ---

    def test_teacher_can_create_student(self):
        student = self.env['college.student'].with_user(self.teacher_user).create({
            'admission_date': date.today(),
            'first_name': 'New',
            'last_name': 'Student',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'communication_address': 'Address',
        })
        self.assertTrue(student.id)

    def test_staff_can_create_student(self):
        student = self.env['college.student'].with_user(self.staff_user).create({
            'admission_date': date.today(),
            'first_name': 'New',
            'last_name': 'Student',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'communication_address': 'Address',
        })
        self.assertTrue(student.id)

    def test_principal_can_create_student(self):
        student = self.env['college.student'].with_user(self.principal_user).create({
            'admission_date': date.today(),
            'first_name': 'New',
            'last_name': 'Student',
            'father_name': 'Father',
            'mother_name': 'Mother',
            'communication_address': 'Address',
        })
        self.assertTrue(student.id)

    # --- Write access ---

    def test_teacher_can_write_student(self):
        student = self._make_student()
        student.with_user(self.teacher_user).write({'first_name': 'Updated'})
        self.assertEqual(student.first_name, 'Updated')

    def test_staff_can_write_student(self):
        student = self._make_student()
        student.with_user(self.staff_user).write({'first_name': 'Updated'})
        self.assertEqual(student.first_name, 'Updated')

    # --- Delete access ---

    def test_teacher_cannot_delete_student(self):
        student = self._make_student()
        with self.assertRaises(AccessError):
            student.with_user(self.teacher_user).unlink()

    def test_staff_cannot_delete_student(self):
        student = self._make_student()
        with self.assertRaises(AccessError):
            student.with_user(self.staff_user).unlink()

    def test_principal_can_delete_student(self):
        student = self._make_student()
        student_id = student.id
        student.with_user(self.principal_user).unlink()
        self.assertFalse(self.env['college.student'].browse(student_id).exists())

    # --- Security group hierarchy ---

    def test_principal_group_implies_staff(self):
        self.assertIn(self.staff_group, self.principal_group.implied_ids)

    def test_staff_group_implies_teacher(self):
        self.assertIn(self.teacher_group, self.staff_group.implied_ids)

    def test_teacher_group_implies_base_user(self):
        base_user_group = self.env.ref('base.group_user')
        self.assertIn(base_user_group, self.teacher_group.implied_ids)
