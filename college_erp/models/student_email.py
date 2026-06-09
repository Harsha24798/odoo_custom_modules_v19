from odoo import models, fields, api


class StudentEmail(models.TransientModel):
    _name = 'student.email'
    _description = 'Send Email to Student'

    student_id = fields.Many2one('college.student', string='Student', readonly=True)
    email_to = fields.Char(string='To', readonly=True)
    subject = fields.Char(string='Subject', required=True)
    body = fields.Html(string='Body', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        student_id = self.env.context.get('default_student_id')
        if student_id:
            student = self.env['college.student'].browse(student_id)
            res['student_id'] = student.id
            res['email_to'] = student.email
        return res

    def action_send(self):
        self.ensure_one()
        self.env['mail.mail'].create({
            'subject': self.subject,
            'email_to': self.email_to,
            'body_html': self.body,
        }).send()
        return {'type': 'ir.actions.act_window_close'}
