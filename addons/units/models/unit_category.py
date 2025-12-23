from odoo import api, fields, models


class UnitCategory(models.Model):
    _name = 'kst.unit.category'
    _description = 'Unit Category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    name = fields.Char('Category Name', required=True, tracking=True, help="e.g., Residential (Condo), Commercial")
    
    # One2many relationships
    unit_ids = fields.One2many('kst.unit', 'category_id', string='Units')
    unit_count = fields.Integer('Number of Units', compute='_compute_unit_count')

    @api.depends('unit_ids')
    def _compute_unit_count(self):
        for record in self:
            record.unit_count = len(record.unit_ids)


