from odoo import fields, models

class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Estate Property Tags'
    _sql_constraints = [
        ('check_name_unique', 'UNIQUE(name)', 'The property tag name must be unique.'),
    ]
    _order = "name"

    name = fields.Char('Tag', required=True)
    color = fields.Integer('Color')
