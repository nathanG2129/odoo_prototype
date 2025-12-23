from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UnitRentTransaction(models.Model):
    _name = 'kst.unit.rent.transaction'
    _description = 'Unit Rent Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "transaction_date desc, id desc"

    # Foreign Keys
    contract_id = fields.Many2one('kst.contract', string='Contract', required=True, ondelete='restrict', tracking=True)
    bank_id = fields.Many2one('kst.bank', string='Bank Account', ondelete='restrict', tracking=True)
    
    # Transaction Information
    transaction_date = fields.Date('Transaction Date', required=True, default=fields.Date.today, tracking=True)
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Payment Status', default='pending', required=True, tracking=True)
    
    # Payment Details
    payment_category = fields.Char('Payment Category', tracking=True, help="e.g., UNIT RENTAL, SECURITY DEPOSIT, ADVANCE RENTAL")
    payment_type = fields.Char('Payment Type', tracking=True, help="e.g., Check, Cash, Bank Transfer")
    payment_reference = fields.Char('Payment Reference', tracking=True, help="Check number, reference number, etc.")
    
    # Financial Fields
    amount_deposited = fields.Float('Amount Deposited', digits=(12, 2), tracking=True)
    
    # Additional Information
    notes = fields.Text('Notes', tracking=True)
    is_bounced = fields.Boolean('Is Bounced', default=False, tracking=True, help="Flag for bounced payments")
    
    # Related Fields for convenience
    unit_id = fields.Many2one('kst.unit', related='contract_id.unit_id', string='Unit', store=True, readonly=True)
    lessee_id = fields.Many2one('kst.lessee', related='contract_id.lessee_id', string='Lessee', store=True, readonly=True)
    lessor_id = fields.Many2one('kst.lessor', related='contract_id.lessor_id', string='Lessor', store=True, readonly=True)

    @api.constrains('amount_deposited')
    def _check_amount(self):
        for record in self:
            if record.amount_deposited < 0:
                raise ValidationError("Amount deposited cannot be negative!")

    def name_get(self):
        result = []
        for record in self:
            contract_name = record.contract_id.contract_number if record.contract_id and record.contract_id.contract_number else f"Contract {record.contract_id.id}" if record.contract_id else 'No Contract'
            date_str = record.transaction_date.strftime('%Y-%m-%d') if record.transaction_date else 'No Date'
            name = f"{contract_name} - {date_str}"
            result.append((record.id, name))
        return result


