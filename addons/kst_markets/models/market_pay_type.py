from odoo import api, fields, models


class MarketPayType(models.Model):
    _name = 'kst.market.pay.type'
    _description = 'Market Payment Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Pay type code must be unique!'),
    ]
    _order = "code"

    code = fields.Char('Pay Type Code', required=True, help="e.g., K1-MH, UGS Weekly, NAWASA, Toilet", tracking=True)
    name = fields.Char('Pay Type Name', required=True, tracking=True)
    pay_type_use = fields.Selection([
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('both', 'Both'),
    ], string='Pay Type Use', required=True, default='electricity', tracking=True)
    sub_group = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Sub-Group', tracking=True)
    
    # One2many relationships to show usage
    stall_electric_ids = fields.One2many('kst.stall', 'electric_pay_type_id', 
                                         string='Stalls (Electric)', readonly=True)
    stall_water_ids = fields.One2many('kst.stall', 'water_pay_type_id', 
                                      string='Stalls (Water)', readonly=True)
    
    # Computed counts
    stall_electric_count = fields.Integer('Stalls (Electric)', compute='_compute_counts', store=False)
    stall_water_count = fields.Integer('Stalls (Water)', compute='_compute_counts', store=False)
    
    @api.depends('stall_electric_ids', 'stall_water_ids')
    def _compute_counts(self):
        for record in self:
            record.stall_electric_count = len(record.stall_electric_ids)
            record.stall_water_count = len(record.stall_water_ids)

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result

