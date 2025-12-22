from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MarketUtilityTransaction(models.Model):
    _name = 'kst.market.utility.transaction'
    _description = 'Market Utility Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "transaction_date desc, id desc"

    # Foreign Keys
    stall_id = fields.Many2one('kst.stall', string='Stall', required=True, ondelete='restrict', tracking=True)
    utility_bill_id = fields.Many2one('kst.utility.bill', string='Utility Bill', 
                                     ondelete='restrict', tracking=True,
                                     help="Provider bill (MERALCO/Water) - if metered billing")
    
    # Transaction Information
    transaction_date = fields.Date('Transaction Date', required=True, default=fields.Date.today, tracking=True)
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Payment Status', default='pending', required=True, tracking=True)
    
    # Utility Information
    utility_type = fields.Selection([
        ('electricity', 'Electricity'),
        ('water', 'Water'),
    ], string='Utility Type', required=True, tracking=True)
    
    # Meter Readings (for metered billing)
    previous_reading = fields.Float('Previous Reading', digits=(12, 2), tracking=True)
    current_reading = fields.Float('Current Reading', digits=(12, 2), tracking=True)
    consumption = fields.Float('Consumption', digits=(12, 2), compute='_compute_consumption', store=True)
    
    # Rate Information (Snapshot Pattern)
    applied_rate = fields.Float('Applied Rate', digits=(12, 6), tracking=True,
                                help="Rate used for this transaction (derived from bill or default rate). Stored for historical accuracy.")
    
    # Financial Fields
    amount_paid = fields.Float('Amount Paid', digits=(12, 2), tracking=True)
    
    # Receipt Information
    receipt_number = fields.Char('Receipt Number', tracking=True)

    # Related Fields for convenience
    market_id = fields.Many2one('kst.market', related='stall_id.market_id', string='Market', store=True, readonly=True)
    tenant_id = fields.Many2one('kst.tenant', related='stall_id.tenant_id', string='Tenant', store=True, readonly=True)
    
    # Computed field to show billing type
    billing_type = fields.Char('Billing Type', compute='_compute_billing_type')

    @api.depends('previous_reading', 'current_reading')
    def _compute_consumption(self):
        for record in self:
            if record.previous_reading and record.current_reading:
                record.consumption = record.current_reading - record.previous_reading
            else:
                record.consumption = 0.0

    @api.depends('utility_bill_id')
    def _compute_billing_type(self):
        for record in self:
            if record.utility_bill_id:
                record.billing_type = 'Metered (From Bill)'
            else:
                record.billing_type = 'Flat Rate'

    @api.constrains('previous_reading', 'current_reading')
    def _check_readings(self):
        for record in self:
            if record.previous_reading and record.current_reading:
                if record.current_reading < record.previous_reading:
                    raise ValidationError("Current reading cannot be less than previous reading!")

    @api.constrains('amount_paid')
    def _check_amount(self):
        for record in self:
            if record.amount_paid < 0:
                raise ValidationError("Amount paid cannot be negative!")

    def name_get(self):
        result = []
        for record in self:
            stall_name = record.stall_id.display_name or 'Unknown Stall'
            date_str = record.transaction_date.strftime('%Y-%m-%d') if record.transaction_date else 'No Date'
            utility = record.utility_type.title() if record.utility_type else 'Unknown'
            name = f"{stall_name} - {utility} - {date_str}"
            result.append((record.id, name))
        return result

