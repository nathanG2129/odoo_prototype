from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Contract(models.Model):
    _name = 'kst.contract'
    _description = 'Rental Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "contract_number desc, id desc"

    # Foreign Keys
    unit_id = fields.Many2one('kst.unit', string='Unit', required=True, ondelete='restrict', tracking=True)
    lessee_id = fields.Many2one('kst.lessee', string='Lessee', required=True, ondelete='restrict', tracking=True)
    lessor_id = fields.Many2one('kst.lessor', string='Lessor', required=True, ondelete='restrict', tracking=True)
    
    # Contract Information
    contract_number = fields.Char('Contract Number', tracking=True)
    period_from = fields.Date('Period From', tracking=True)
    period_to = fields.Date('Period To', tracking=True)
    
    # Financial Fields
    basic_rent = fields.Float('Basic Rent', digits=(12, 2), tracking=True)
    evat = fields.Float('eVAT', digits=(12, 2), tracking=True, help="Electronic Value Added Tax")
    withholding_tax = fields.Float('Withholding Tax', digits=(12, 2), tracking=True)
    mptr = fields.Float('MPTR', digits=(12, 2), tracking=True, help="Monthly Percentage Tax Rate")
    monthly_rate = fields.Float('Monthly Rate', digits=(12, 2), compute='_compute_monthly_rate', store=True, tracking=True, help="Basic Rent + eVAT + Withholding Tax")
    cusa_rate = fields.Float('CUSA Rate', digits=(12, 2), tracking=True, help="Common Use Service Area Rate")
    
    # Escalation Terms
    escalation_percentage = fields.Float('Escalation Percentage', digits=(5, 2), tracking=True, help="Percentage increase")
    escalation_date_months = fields.Integer('Escalation Date (Months)', tracking=True, help="Interval in months for escalation")
    
    # Additional Information
    notes = fields.Text('Notes', tracking=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Status', default='active', required=True, tracking=True)
    
    # One2many relationships
    transaction_ids = fields.One2many('kst.unit.rent.transaction', 'contract_id', string='Rent Transactions')
    transaction_count = fields.Integer('Number of Transactions', compute='_compute_transaction_count')

    @api.depends('basic_rent', 'evat', 'withholding_tax')
    def _compute_monthly_rate(self):
        for record in self:
            record.monthly_rate = (record.basic_rent or 0) + (record.evat or 0) + (record.withholding_tax or 0)

    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        for record in self:
            record.transaction_count = len(record.transaction_ids)

    @api.constrains('period_from', 'period_to')
    def _check_period(self):
        for record in self:
            if record.period_from and record.period_to:
                if record.period_to < record.period_from:
                    raise ValidationError("Period To cannot be earlier than Period From!")

    def name_get(self):
        result = []
        for record in self:
            unit_name = record.unit_id.full_code if record.unit_id else 'Unknown Unit'
            lessee_name = record.lessee_id.name if record.lessee_id else 'Unknown Lessee'
            if record.contract_number:
                name = f"[{record.contract_number}] {unit_name} - {lessee_name}"
            else:
                name = f"{unit_name} - {lessee_name}"
            result.append((record.id, name))
        return result


