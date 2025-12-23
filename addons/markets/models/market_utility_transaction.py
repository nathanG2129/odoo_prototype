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
    applied_rate = fields.Float('Applied Rate', digits=(12, 2), tracking=True,
                                help="Rate used for this transaction (derived from bill or default rate). Stored for historical accuracy.")
    
    # Financial Fields
    amount_due = fields.Float('Amount Due', digits=(12, 2), compute='_compute_amount_due', store=True,
                              help="Expected amount due based on applied rate or default stall rate")
    amount_paid = fields.Float('Amount Paid', digits=(12, 2), tracking=True)
    soa_issuable = fields.Boolean('SOA Issuable', compute='_compute_soa_issuable', store=False,
                                  help="True when this transaction is underpaid and can have an SOA issued")
    
    # Receipt Information
    receipt_number = fields.Char('Receipt Number', tracking=True)

    # Related Fields for convenience
    market_id = fields.Many2one('kst.market', related='stall_id.market_id', string='Market', store=True, readonly=True)
    tenant_id = fields.Many2one('kst.tenant', related='stall_id.tenant_id', string='Tenant', store=True, readonly=True)
    
    # Pay Type Frequency (sub-group) - related field based on utility type
    pay_type_frequency = fields.Char('Frequency', compute='_compute_pay_type_frequency', store=False,
                                     help="Payment frequency (daily/weekly/monthly) from pay type")
    
    # Computed field to show billing type
    billing_type = fields.Char('Billing Type', compute='_compute_billing_type')
    
    @api.depends('stall_id', 'utility_type', 'stall_id.electric_pay_type_id', 'stall_id.water_pay_type_id',
                 'stall_id.electric_pay_type_id.sub_group', 'stall_id.water_pay_type_id.sub_group')
    def _compute_pay_type_frequency(self):
        """Get the pay type frequency (sub-group) based on utility type"""
        for record in self:
            if not record.stall_id:
                record.pay_type_frequency = ''
                continue
            
            pay_type = None
            if record.utility_type == 'electricity':
                pay_type = record.stall_id.electric_pay_type_id
            elif record.utility_type == 'water':
                pay_type = record.stall_id.water_pay_type_id
            
            if pay_type and pay_type.sub_group:
                # Convert selection value to display label
                selection_dict = dict(pay_type._fields['sub_group'].selection)
                record.pay_type_frequency = selection_dict.get(pay_type.sub_group, pay_type.sub_group)
            else:
                record.pay_type_frequency = ''

    @api.depends('previous_reading', 'current_reading')
    def _compute_consumption(self):
        for record in self:
            if record.previous_reading and record.current_reading:
                record.consumption = record.current_reading - record.previous_reading
            else:
                record.consumption = 0.0
    
    @api.onchange('stall_id', 'utility_type')
    def _onchange_stall_set_default_rate(self):
        """Set applied_rate to default rate from stall when stall or utility type changes"""
        for record in self:
            # Only set if applied_rate is not already set (0 or None)
            if not record.applied_rate or record.applied_rate == 0:
                if record.stall_id:
                    if record.utility_type == 'electricity':
                        record.applied_rate = record.stall_id.default_electricity_rate or 0.0
                    elif record.utility_type == 'water':
                        record.applied_rate = record.stall_id.default_water_rate or 0.0
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
                stall_id = vals.get('stall_id')
                utility_type = vals.get('utility_type')
                
                if stall_id and utility_type:
                    stall = self.env['kst.stall'].browse(stall_id)
                    if utility_type == 'electricity':
                        vals['applied_rate'] = stall.default_electricity_rate or 0.0
                    elif utility_type == 'water':
                        vals['applied_rate'] = stall.default_water_rate or 0.0
        
        return super().create(vals_list)
    
    @api.depends('applied_rate', 'consumption', 'previous_reading', 'current_reading', 
                 'stall_id', 'utility_type', 
                 'stall_id.default_electricity_rate', 'stall_id.default_water_rate')
    def _compute_amount_due(self):
        """Compute amount due based on consumption × rate (if metered) or flat rate"""
        for record in self:
            if not record.stall_id:
                record.amount_due = 0.0
                continue
            
            # Determine the rate to use
            rate = 0.0
            if record.applied_rate and record.applied_rate > 0:
                # Use applied rate if available
                rate = record.applied_rate
            else:
                # Use default rate from stall based on utility type
                if record.utility_type == 'electricity':
                    rate = record.stall_id.default_electricity_rate or 0.0
                elif record.utility_type == 'water':
                    rate = record.stall_id.default_water_rate or 0.0
            
            # Calculate consumption directly from readings (to ensure it's up-to-date when editing inline)
            consumption = 0.0
            if record.previous_reading and record.current_reading:
                consumption = record.current_reading - record.previous_reading
            elif record.consumption:
                # Fallback to stored consumption if readings aren't available
                consumption = record.consumption
            
            # Calculate amount due: consumption × rate (if consumption exists), otherwise flat rate
            if consumption and consumption > 0:
                # Metered billing: consumption × rate
                record.amount_due = consumption * rate
            else:
                # Flat rate billing: just the rate (no consumption to multiply)
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

    def action_generate_soa(self):
        """Prototype action to 'generate' an SOA for a single transaction.

        For now, this just raises a client notification. Later this can
        trigger a report or document generation.
        """
        self.ensure_one()

        if not self.soa_issuable:
            # Safety check: don't generate SOA when not underpaid
            raise ValidationError("SOA cannot be generated: this transaction is not underpaid.")

        stall_name = self.stall_id.display_name or 'Stall'
        date_str = self.transaction_date or 'no date'
        message = (
            "SOA can be issued for %s on %s. "
            "This is a prototype action; hook this into a real report later."
        ) % (stall_name, date_str)

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
            stall_name = record.stall_id.display_name or 'Unknown Stall'
            date_str = record.transaction_date.strftime('%Y-%m-%d') if record.transaction_date else 'No Date'
            utility = record.utility_type.title() if record.utility_type else 'Unknown'
            name = f"{stall_name} - {utility} - {date_str}"
            result.append((record.id, name))
        return result

