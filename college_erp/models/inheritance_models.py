from odoo import fields, models

class InheritanceSaleOrder(models.Model):
    _inherit = 'sale.order'

    student_id = fields.Many2one('college.student', string='Student')