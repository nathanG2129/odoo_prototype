from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UnitUtilityTransaction(models.Model):
    _name = 'kst.unit.utility.transaction'
    _description = 'Unit Utility Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "transaction_date desc, id desc"

    # Foreign Keys
    unit_id = fields.Many2one('kst.unit', string='Unit', required=True, ondelete='restrict', tracking=True)
    utility_bill_id = fields.Many2one('kst.unit.utility.bill', string='Utility Bill', 
                                     ondelete='restrict', tracking=True,
                                     help="Provider bill (MERALCO/Water) - if metered billing")
    
    # Transaction Information
    transaction_date = fields.Date('Transaction Date', required=True, default=fields.Date.today, tracking=True)
    
    # Verification Status (for manager review)
    verification_status = fields.Selection([
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('check_bounced', 'Check Bounced'),
        ('rejected', 'Rejected'),
    ], string='Verification Status', default='pending', required=True, tracking=True,
       help="Manager verification status for payment review")
    
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
    applied_rate = fields.Float('Applied Rate', digits=(12, 2), tracking=True,
                                help="Rate used for this transaction (derived from bill or default rate). Stored for historical accuracy.")
    
    # Financial Fields
    amount_due = fields.Float('Amount Due', digits=(12, 2), compute='_compute_amount_due', store=True,
                              help="Expected amount due based on applied rate or default unit rate")
    amount_paid = fields.Float('Amount Paid', digits=(12, 2), tracking=True)
    soa_issuable = fields.Boolean('SOA Issuable', compute='_compute_soa_issuable', store=False,
                                  help="True when this transaction is underpaid and can have an SOA issued")
    
    # Receipt Information
    receipt_number = fields.Char('Receipt Number', tracking=True)
    
    # Payment Attachments (receipts, deposit slips, etc.)
    attachment_ids = fields.One2many(
        'kst.payment.attachment',
        'unit_utility_transaction_id',
        string='Attachments',
        help="Upload payment receipts, deposit slips, GCash/Maya screenshots, etc."
    )
    attachment_count = fields.Integer('Attachment Count', compute='_compute_attachment_count', store=False)

    # Related Fields for convenience
    lessor_id = fields.Many2one('kst.lessor', related='unit_id.lessor_id', string='Lessor', store=True, readonly=True)
    location_id = fields.Many2one('kst.location', related='unit_id.location_id', string='Location', store=True, readonly=True)
    
    # Computed field to show billing type
    billing_type = fields.Char('Billing Type', compute='_compute_billing_type')
    
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.depends('previous_reading', 'current_reading')
    def _compute_consumption(self):
        for record in self:
            if record.previous_reading and record.current_reading:
                record.consumption = record.current_reading - record.previous_reading
            else:
                record.consumption = 0.0
    
    @api.onchange('unit_id', 'utility_type')
    def _onchange_unit_set_default_rate(self):
        """Set applied_rate to default rate from unit when unit or utility type changes"""
        for record in self:
            # Only set if applied_rate is not already set (0 or None)
            if not record.applied_rate or record.applied_rate == 0:
                if record.unit_id:
                    if record.utility_type == 'electricity':
                        record.applied_rate = record.unit_id.default_electricity_rate or 0.0
                    elif record.utility_type == 'water':
                        record.applied_rate = record.unit_id.default_water_rate or 0.0
                    else:
                        record.applied_rate = 0.0
                else:
                    record.applied_rate = 0.0
    
    @api.model_create_multi
    def create(self, vals_list):
        """Set applied_rate to default rate when creating new records"""
        for vals in vals_list:
            # Only set if applied_rate is not provided or is 0
            if 'applied_rate' not in vals or not vals.get('applied_rate') or vals.get('applied_rate') == 0:
                unit_id = vals.get('unit_id')
                utility_type = vals.get('utility_type')
                
                if unit_id and utility_type:
                    unit = self.env['kst.unit'].browse(unit_id)
                    if utility_type == 'electricity':
                        vals['applied_rate'] = unit.default_electricity_rate or 0.0
                    elif utility_type == 'water':
                        vals['applied_rate'] = unit.default_water_rate or 0.0
        
        return super().create(vals_list)
    
    @api.depends('applied_rate', 'consumption', 'previous_reading', 'current_reading', 
                 'unit_id', 'utility_type',
                 'unit_id.default_electricity_rate', 'unit_id.default_water_rate')
    def _compute_amount_due(self):
        """Compute amount due based on consumption × rate (if metered) or flat rate."""
        for record in self:
            if not record.unit_id:
                record.amount_due = 0.0
                continue
            
            # Determine the rate to use
            rate = 0.0
            if record.applied_rate and record.applied_rate > 0:
                # Use applied rate if available
                rate = record.applied_rate
            else:
                # Use default rate from unit based on utility type
                if record.utility_type == 'electricity':
                    rate = record.unit_id.default_electricity_rate or 0.0
                elif record.utility_type == 'water':
                    rate = record.unit_id.default_water_rate or 0.0
            
            # Calculate consumption directly from readings
            consumption = 0.0
            if record.previous_reading and record.current_reading:
                consumption = record.current_reading - record.previous_reading
            elif record.consumption:
                consumption = record.consumption
            
            # Calculate amount due: consumption × rate (if consumption exists), otherwise flat rate
            if consumption and consumption > 0:
                record.amount_due = consumption * rate
            else:
                record.amount_due = rate

    @api.depends('amount_due', 'amount_paid')
    def _compute_soa_issuable(self):
        """A transaction is SOA-issuable when it has a positive amount_due and is underpaid."""
        for record in self:
            due = record.amount_due or 0.0
            paid = record.amount_paid or 0.0
            record.soa_issuable = due > 0 and paid < due

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

    def action_verify(self):
        """Mark transaction as verified by manager"""
        self.ensure_one()
        if self.verification_status != 'pending':
            raise ValidationError("Only pending transactions can be verified!")
        self.verification_status = 'verified'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Transaction Verified',
                'message': 'Payment has been verified.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_check_bounced(self):
        """Mark transaction as check bounced"""
        self.ensure_one()
        if self.verification_status != 'pending':
            raise ValidationError("Only pending transactions can be marked as check bounced!")
        self.verification_status = 'check_bounced'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Check Bounced',
                'message': 'Payment has been marked as check bounced.',
                'type': 'warning',
                'sticky': False,
            }
        }
    
    def action_reject(self):
        """Reject the transaction"""
        self.ensure_one()
        if self.verification_status != 'pending':
            raise ValidationError("Only pending transactions can be rejected!")
        self.verification_status = 'rejected'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Transaction Rejected',
                'message': 'Payment has been rejected.',
                'type': 'warning',
                'sticky': False,
            }
        }
    
    def action_generate_soa(self):
        """Prototype action to 'generate' an SOA for a single transaction."""
        self.ensure_one()

        if not self.soa_issuable:
            raise ValidationError("SOA cannot be generated: this transaction is not underpaid.")

        unit_name = self.unit_id.display_name or 'Unit'
        date_str = self.transaction_date or 'no date'
        message = (
            "SOA can be issued for %s on %s. "
            "This is a prototype action; hook this into a real report later."
        ) % (unit_name, date_str)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SOA Generation (Prototype)',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def name_get(self):
        result = []
        for record in self:
            unit_name = record.unit_id.display_name or 'Unknown Unit'
            date_str = record.transaction_date.strftime('%Y-%m-%d') if record.transaction_date else 'No Date'
            utility = record.utility_type.title() if record.utility_type else 'Unknown'
            name = f"{unit_name} - {utility} - {date_str}"
            result.append((record.id, name))
        return result

