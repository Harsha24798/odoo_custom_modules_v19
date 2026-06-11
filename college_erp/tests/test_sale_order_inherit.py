from odoo.tests import TransactionCase
from datetime import date


class TestSaleOrderInherit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.student = self.env['college.student'].create({
            'admission_date': date.today(),
            'first_name': 'Bob',
            'last_name': 'Jones',
            'father_name': 'Tom Jones',
            'mother_name': 'Sue Jones',
            'communication_address': '789 Pine Rd',
        })
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})

    def test_sale_order_has_student_id_field(self):
        self.assertIn('student_id', self.env['sale.order']._fields)

    def test_student_id_comodel_is_college_student(self):
        field = self.env['sale.order']._fields['student_id']
        self.assertEqual(field.comodel_name, 'college.student')

    def test_sale_order_can_be_linked_to_student(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'student_id': self.student.id,
        })
        self.assertEqual(order.student_id, self.student)

    def test_sale_order_student_id_is_optional(self):
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.assertFalse(order.student_id)

    def test_sale_order_student_id_can_be_updated(self):
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        order.student_id = self.student
        self.assertEqual(order.student_id, self.student)

    def test_sale_order_student_id_can_be_cleared(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'student_id': self.student.id,
        })
        order.student_id = False
        self.assertFalse(order.student_id)
