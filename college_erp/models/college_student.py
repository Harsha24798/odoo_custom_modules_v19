from odoo import models, fields, api
from datetime import date
from odoo.exceptions import ValidationError

class CollegeStudent(models.Model):
    _name = 'college.student'
    _description = 'College Student Details'
    _rec_name = 'admission_no'

    _admission_no_unique = models.Constraint(
        'UNIQUE(admission_no)',
        'Admission number must be unique.',
    )

    admission_no = fields.Char(
        string='Admission Number', required=True,
        copy=False, readonly=True, default='New', index=True,
    )
    admission_date = fields.Date(string='Admission Date', required=True)
    first_name = fields.Char(string='First Name', required=True)
    last_name = fields.Char(string='Last Name', required=True)
    father_name = fields.Char(string='Father\'s Name', required=True)
    mother_name = fields.Char(string='Mother\'s Name', required=True)
    communication_address = fields.Text(string='Communication Address', required=True)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state', 'Fed. State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country')
    country_code = fields.Char(related='country_id.code', string='Country Code')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    same_as_communication = fields.Boolean('Same as Communication', default=True)
    image_1920 = fields.Image(string='Student Image')
    birth_day = fields.Date(string='Birth Day')
    age = fields.Integer(string='Age', compute='_compute_age')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('admission_no', 'New') == 'New':
                vals['admission_no'] = (
                    self.env['ir.sequence'].next_by_code('college.student.admission.no') or 'New'
                )
        return super().create(vals_list)

    def write(self, vals):
        if 'admission_no' in vals and self.env['college.student'].search_count(
            [('admission_no', '=', vals['admission_no']), ('id', 'not in', self.ids)],
            limit=1,
        ):
            raise ValidationError('Admission number must be unique.')
        return super().write(vals)

    def action_rainbow_effect(self):
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'This is the rainbow effect',
                'img_url': '/web/static/img/smile.svg',
                'type': 'rainbow_man'
            }
        }

    @api.depends('birth_day')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.birth_day:
                record.age = (
                    today.year - record.birth_day.year
                    - ((today.month, today.day) < (record.birth_day.month, record.birth_day.day))
                )
            else:
                record.age = 0

    def action_send_email(self):
        self.ensure_one()
        return {
            'name': 'Send Email',
            'type': 'ir.actions.act_window',
            'res_model': 'student.email',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_student_id': self.id},
        }