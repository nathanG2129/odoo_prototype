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
    stall_id = fields.Many2one('kst.stall', string='Stall', required=True, ondelete='restrict', tracking=True)
    
    # Transaction Information
    transaction_date = fields.Date('Transaction Date', required=True, default=fields.Date.today, tracking=True)
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Payment Status', default='pending', required=True, tracking=True)
    
    # Financial Fields
    rent_paid = fields.Float('Rent Paid', digits=(12, 2), tracking=True)
    cobp_due = fields.Float('COBP Due', digits=(12, 2), help="Cash on Billing Period Due", tracking=True)
    cobp_paid = fields.Float('COBP Paid', digits=(12, 2), help="Cash on Billing Period Paid", tracking=True)
    
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

    @api.constrains('rent_paid', 'cobp_due', 'cobp_paid')
    def _check_amounts(self):
        for record in self:
            if record.rent_paid < 0:
                raise ValidationError("Rent paid cannot be negative!")
            if record.cobp_due < 0:
                raise ValidationError("COBP Due cannot be negative!")
            if record.cobp_paid < 0:
                raise ValidationError("COBP Paid cannot be negative!")

    def name_get(self):
        result = []
        for record in self:
            stall_name = record.stall_id.display_name or 'Unknown Stall'
            date_str = record.transaction_date.strftime('%Y-%m-%d') if record.transaction_date else 'No Date'
            name = f"{stall_name} - {date_str}"
            result.append((record.id, name))
        return result

