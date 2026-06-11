from odoo.tests import TransactionCase
from datetime import date


class TestStudentEmail(TransactionCase):

    def setUp(self):
        super().setUp()
        self.student = self.env['college.student'].create({
            'admission_date': date.today(),
            'first_name': 'Alice',
            'last_name': 'Smith',
            'father_name': 'Bob Smith',
            'mother_name': 'Carol Smith',
            'communication_address': '456 Oak Ave',
            'email': 'alice@example.com',
        })

    def _make_wizard(self, subject='Test Subject', body='<p>Hello</p>'):
        return self.env['student.email'].with_context(
            default_student_id=self.student.id
        ).create({'subject': subject, 'body': body})

    # --- default_get ---

    def test_default_get_sets_student_id(self):
        wizard = self._make_wizard()
        self.assertEqual(wizard.student_id, self.student)

    def test_default_get_sets_email_to_from_student(self):
        wizard = self._make_wizard()
        self.assertEqual(wizard.email_to, 'alice@example.com')

    def test_default_get_sets_email_from_current_user(self):
        wizard = self._make_wizard()
        self.assertEqual(wizard.email_from, self.env.user.email)

    def test_default_get_no_context_leaves_student_empty(self):
        wizard = self.env['student.email'].create({
            'subject': 'No Student',
            'body': '<p>body</p>',
        })
        self.assertFalse(wizard.student_id)

    def test_default_get_student_without_email_sets_empty_email_to(self):
        student_no_email = self.env['college.student'].create({
            'admission_date': date.today(),
            'first_name': 'Bob',
            'last_name': 'Jones',
            'father_name': 'Tom Jones',
            'mother_name': 'Sue Jones',
            'communication_address': '789 Pine Rd',
        })
        wizard = self.env['student.email'].with_context(
            default_student_id=student_no_email.id
        ).create({'subject': 'Test', 'body': '<p>Hi</p>'})
        self.assertFalse(wizard.email_to)

    # --- action_send ---

    def test_action_send_returns_act_window_close(self):
        wizard = self._make_wizard()
        result = wizard.action_send()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')

    def test_action_send_includes_rainbow_effect(self):
        wizard = self._make_wizard()
        result = wizard.action_send()
        self.assertIn('effect', result)
        self.assertEqual(result['effect']['type'], 'rainbow_man')

    def test_action_send_creates_mail_mail_record(self):
        wizard = self._make_wizard(subject='Unique Subject For Test')
        wizard.action_send()
        mail = self.env['mail.mail'].search([('subject', '=', 'Unique Subject For Test')])
        self.assertTrue(mail, 'Expected a mail.mail record to be created')

    def test_action_send_mail_has_correct_recipients(self):
        wizard = self._make_wizard(subject='Recipient Check')
        wizard.action_send()
        mail = self.env['mail.mail'].search([('subject', '=', 'Recipient Check')], limit=1)
        self.assertEqual(mail.email_to, 'alice@example.com')
