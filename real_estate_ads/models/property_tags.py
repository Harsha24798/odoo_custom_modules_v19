from odoo import models, fields


class PropertyTags(models.Model):
    _name = 'estate.property.tags'
    _description = 'Property Tags'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color', default=0)

