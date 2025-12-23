from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Location(models.Model):
    _name = 'kst.location'
    _description = 'Unit Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Location code must be unique!'),
    ]
    _order = "code"

    code = fields.Char('Location Code', required=True, tracking=True)
    description = fields.Char('Location Description', tracking=True)
    company_name = fields.Char('Company Name', tracking=True)
    company_code = fields.Char('Company Code', tracking=True)
    company_address = fields.Text('Company Address', tracking=True)
    
    # One2many relationships
    unit_ids = fields.One2many('kst.unit', 'location_id', string='Units')
    unit_count = fields.Integer('Number of Units', compute='_compute_unit_count')

    @api.depends('unit_ids')
    def _compute_unit_count(self):
        for record in self:
            record.unit_count = len(record.unit_ids)

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.description or record.company_name or 'Location'}"
            result.append((record.id, name))
        return result


