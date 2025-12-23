from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Market(models.Model):
    _name = 'kst.market'
    _description = 'Market'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Market code must be unique!'),
    ]
    _order = "code"

    code = fields.Char('Market Code', required=True, tracking=True)
    name = fields.Char('Market Name', required=True, tracking=True)
    address = fields.Text('Address', tracking=True)
    
    # One2many relationships
    stall_ids = fields.One2many('kst.stall', 'market_id', string='Stalls')
    stall_count = fields.Integer('Number of Stalls', compute='_compute_stall_count')

    @api.depends('stall_ids')
    def _compute_stall_count(self):
        for record in self:
            record.stall_count = len(record.stall_ids)

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result

