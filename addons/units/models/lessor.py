from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Lessor(models.Model):
    _name = 'kst.lessor'
    _description = 'Lessor (Property Owner)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Lessor code must be unique!'),
    ]
    _order = "code"

    code = fields.Char('Lessor Code', required=True, tracking=True)
    name = fields.Char('Lessor Name', required=True, tracking=True)
    
    # One2many relationships
    unit_ids = fields.One2many('kst.unit', 'lessor_id', string='Units')
    contract_ids = fields.One2many('kst.contract', 'lessor_id', string='Contracts')
    unit_count = fields.Integer('Number of Units', compute='_compute_counts')
    contract_count = fields.Integer('Number of Contracts', compute='_compute_counts')

    @api.depends('unit_ids', 'contract_ids')
    def _compute_counts(self):
        for record in self:
            record.unit_count = len(record.unit_ids)
            record.contract_count = len(record.contract_ids)

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result


