from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MarketRentTransaction(models.Model):
    _name = 'kst.market.rent.transaction'
    _description = 'Market Rent Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "transaction_date desc, id desc"
    
    # Mail.thread automatically adds these fields:
    # - message_ids (One2many to mail.message)
    # - message_follower_ids (One2many to mail.followers)
    # - activity_ids (One2many to mail.activity)
    # - message_main_attachment_id (Many2one to ir.attachment)

    # Foreign Keys
    stall_id = fields.Many2one(
        'kst.stall',
        string='Stall',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    rent_batch_id = fields.Many2one(
        'kst.market.rent.batch',
        string='Rent Batch',
        ondelete='restrict',
        tracking=True,
        help="Rent batch (Market + Date + Collection Type) that this transaction belongs to.",
    )
    
    # Transaction Information
    transaction_date = fields.Date('Transaction Date', required=True, default=fields.Date.today, tracking=True)
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Payment Status', default='pending', required=True, tracking=True)
    
    # Verification Status (for manager review)
    verification_status = fields.Selection([
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ], string='Verification Status', default='pending', required=True, tracking=True,
       help="Manager verification status for payment review")
    
    # Financial Fields
    rent_paid = fields.Float('Rent Paid', digits=(12, 2), tracking=True)
    copb_due = fields.Float('COPB Due', digits=(12, 2), help="Collection on Previous Balance Due", tracking=True)
    copb_paid = fields.Float('COPB Paid', digits=(12, 2), help="Collection on Previous Balance Paid", tracking=True)
    
    # Receipt Information
    receipt_number = fields.Char('Receipt Number', tracking=True)
    
    # Note: Odoo automatically provides create_uid, create_date, write_uid, write_date
    # No need for custom encoded_by/encoded_date fields
    
    # Related Fields for convenience
    market_id = fields.Many2one('kst.market', related='stall_id.market_id', string='Market', store=True, readonly=True)
    tenant_id = fields.Many2one('kst.tenant', related='stall_id.tenant_id', string='Tenant', store=True, readonly=True)
    rent_collection_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], related='stall_id.rent_collection_type', string='Rent Collection Type', store=True, readonly=True)
    rent = fields.Float(related='stall_id.rental_rate', string='Rent', store=True, readonly=True, digits=(12, 2))

    @api.constrains('rent_paid', 'copb_due', 'copb_paid')
    def _check_amounts(self):
        for record in self:
            if record.rent_paid < 0:
                raise ValidationError("Rent paid cannot be negative!")
            if record.copb_due < 0:
                raise ValidationError("COPB Due cannot be negative!")
            if record.copb_paid < 0:
                raise ValidationError("COPB Paid cannot be negative!")

    def action_verify(self):
        """Verify the payment transaction."""
        self.ensure_one()
        if self.verification_status != 'pending':
            raise ValidationError("Only pending transactions can be verified!")
        self.verification_status = 'verified'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Payment Verified',
                'message': 'The payment has been verified.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_reject(self):
        """Reject the payment transaction."""
        self.ensure_one()
        if self.verification_status != 'pending':
            raise ValidationError("Only pending transactions can be rejected!")
        self.verification_status = 'rejected'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Payment Rejected',
                'message': 'The payment has been rejected.',
                'type': 'danger',
                'sticky': False,
            }
        }

    def name_get(self):
        result = []
        for record in self:
            stall_name = record.stall_id.display_name or 'Unknown Stall'
            date_str = record.transaction_date.strftime('%Y-%m-%d') if record.transaction_date else 'No Date'
            name = f"{stall_name} - {date_str}"
            result.append((record.id, name))
        return result

