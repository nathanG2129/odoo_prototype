from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Unit(models.Model):
    _name = 'kst.unit'
    _description = 'Rental Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "full_code"

    # Foreign Keys
    lessor_id = fields.Many2one('kst.lessor', string='Lessor', required=True, ondelete='restrict', tracking=True)
    category_id = fields.Many2one('kst.unit.category', string='Category', ondelete='restrict', tracking=True)
    location_id = fields.Many2one('kst.location', string='Location', ondelete='restrict', tracking=True)
    bank_id = fields.Many2one('kst.bank', string='Bank Account', ondelete='restrict', tracking=True)
    kcode_id = fields.Many2one('kst.kcode', string='KCode', ondelete='restrict', tracking=True, help="Unit identifier code (e.g., RET)")
    
    # Basic Fields
    unit_specified = fields.Char('Unit Specified', tracking=True, help="Specific unit number (e.g., 2)")
    full_code = fields.Char('Full Code', compute='_compute_full_code', store=True, help="KCode + Unit Specified (e.g., RET-2)")
    address = fields.Text('Unit Address', tracking=True)
    description = fields.Text('Description', tracking=True, help="Type of Use in Legacy")
    size = fields.Float('Size', digits=(12, 2), tracking=True)
    soa_bank_account_number = fields.Char('SOA Bank Account Number', tracking=True, help="Statement of Account bank account")
    
    # One2many relationships
    contract_ids = fields.One2many('kst.contract', 'unit_id', string='Contracts')
    contract_count = fields.Integer('Number of Contracts', compute='_compute_contract_count')

    @api.depends('kcode_id', 'kcode_id.code', 'unit_specified')
    def _compute_full_code(self):
        for record in self:
            if record.kcode_id and record.unit_specified:
                record.full_code = f"{record.kcode_id.code}-{record.unit_specified}"
            elif record.kcode_id:
                record.full_code = record.kcode_id.code
            elif record.unit_specified:
                record.full_code = record.unit_specified
            else:
                record.full_code = 'New Unit'

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for record in self:
            record.contract_count = len(record.contract_ids)

    def name_get(self):
        result = []
        for record in self:
            if record.full_code and record.full_code != 'New Unit':
                name = record.full_code
            else:
                name = f"Unit {record.id}"
            result.append((record.id, name))
        return result

