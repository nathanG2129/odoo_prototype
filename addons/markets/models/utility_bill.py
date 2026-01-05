from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta


class UtilityBill(models.Model):
    _name = 'kst.utility.bill'
    _description = 'Utility Bill'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "bill_date desc, id desc"

    # Foreign Keys
    utility_account_id = fields.Many2one('kst.utility.account', string='Utility Account', 
                                        required=True, ondelete='restrict', tracking=True)

    # Bill Information
    bill_date = fields.Date('Bill Date', required=True, tracking=True)
    due_date = fields.Date('Due Date', tracking=True)
    period_covered_from = fields.Date('Period Covered From', required=True, tracking=True)
    period_covered_to = fields.Date('Period Covered To', required=True, tracking=True)
    
    # Billing Details
    total_consumption = fields.Float('Total Consumption', digits=(12, 2), tracking=True,
                                    help="Total consumption for the billing period")
    total_bill_amount = fields.Float('Total Bill Amount', digits=(12, 2), default=0.0, tracking=True,
                                     help="Total amount from utility provider")
    derived_rate = fields.Float('Derived Rate', digits=(12, 2), compute='_compute_derived_rate', 
                                store=True, tracking=True,
                                help="Calculated rate per unit (Total Bill / Total Consumption)")
    
    # Related Fields
    utility_type = fields.Selection(related='utility_account_id.utility_type', string='Utility Type', 
                                   store=True, readonly=True)
    utility_account_number = fields.Char(related='utility_account_id.utility_account_number', 
                                        string='Account Number', store=True, readonly=True)
    
    # Collection Status Workflow
    collection_status = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('verified', 'Verified'),
        ('check_bounced', 'Check Bounced'),
        ('rejected', 'Rejected'),
    ], string='Collection Status', default='draft', required=True, tracking=True,
       help="Workflow status: Draft > Published > Verified/Bounced/Rejected")
    
    # One2many relationship to transactions
    transaction_ids = fields.One2many('kst.market.utility.transaction', 'utility_bill_id', 
                                     string='Utility Transactions')
    transaction_count = fields.Integer('Transaction Count', compute='_compute_transaction_count')
    has_underpayment = fields.Boolean('Has Underpayment', compute='_compute_has_underpayment', store=False,
                                      help="True when any transaction has amount_paid < amount_due")
    
    # Financial Summary (computed from transactions)
    total_amount_paid = fields.Float('Total Amount Paid', digits=(12, 2), compute='_compute_financial_summary', 
                                    store=False, help="Total amount collected from all transactions")
    profit_loss = fields.Float('Profit & Loss', digits=(12, 2), compute='_compute_financial_summary', 
                               store=False, help="Difference between amount paid and bill amount (Paid - Bill)")
    
    stall_count = fields.Integer('Stall Count', compute='_compute_stall_count', store=False,
                                 help="Number of active stalls assigned to this utility account")

    @api.depends('total_bill_amount', 'total_consumption')
    def _compute_derived_rate(self):
        for record in self:
            if record.total_consumption and record.total_consumption > 0:
                record.derived_rate = record.total_bill_amount / record.total_consumption
            else:
                record.derived_rate = 0.0

    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        for record in self:
            record.transaction_count = len(record.transaction_ids)
    
    @api.depends('transaction_ids.amount_paid', 'transaction_ids.amount_due')
    def _compute_has_underpayment(self):
        for record in self:
            record.has_underpayment = any(
                (t.amount_due or 0.0) > (t.amount_paid or 0.0)
                for t in record.transaction_ids
            )
    
    @api.depends('utility_account_id')
    def _compute_stall_count(self):
        for record in self:
            if record.utility_account_id:
                # Access stalls through reverse relationship
                stalls = self.env['kst.stall'].search([
                    ('utility_account_id', '=', record.utility_account_id.id),
                    ('is_active', '=', True)
                ])
                record.stall_count = len(stalls)
            else:
                record.stall_count = 0
    
    @api.depends('transaction_ids', 'transaction_ids.amount_paid', 'total_bill_amount')
    def _compute_financial_summary(self):
        """Compute total amount paid and profit/loss"""
        for record in self:
            total_paid = sum(record.transaction_ids.mapped('amount_paid') or [0.0])
            record.total_amount_paid = total_paid
            record.profit_loss = total_paid - record.total_bill_amount

    def action_publish(self):
        """Publish the utility bill for collection"""
        self.ensure_one()
        if self.collection_status != 'draft':
            raise ValidationError("Only draft bills can be published!")
        self.collection_status = 'published'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Bill Published',
                'message': 'Utility bill has been published and is ready for collection.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_verify(self):
        """Verify the utility bill after all payments are collected"""
        self.ensure_one()
        if self.collection_status != 'published':
            raise ValidationError("Only published bills can be verified!")
        self.collection_status = 'verified'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Bill Verified',
                'message': 'Utility bill has been verified.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_check_bounced(self):
        """Mark bill as check bounced"""
        self.ensure_one()
        if self.collection_status != 'published':
            raise ValidationError("Only published bills can be marked as check bounced!")
        self.collection_status = 'check_bounced'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Check Bounced',
                'message': 'Utility bill has been marked as check bounced.',
                'type': 'warning',
                'sticky': False,
            }
        }
    
    def action_reject(self):
        """Reject the utility bill"""
        self.ensure_one()
        if self.collection_status != 'published':
            raise ValidationError("Only published bills can be rejected!")
        self.collection_status = 'rejected'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Bill Rejected',
                'message': 'Utility bill has been rejected.',
                'type': 'warning',
                'sticky': False,
            }
        }
    
    def action_generate_soa(self):
        """Prototype: trigger SOA generation placeholder.

        For now, just notify the user. In a full implementation, this would
        render or queue an SOA report.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SOA Requested',
                'message': 'Generate SOA prototype triggered (placeholder).',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.constrains('total_bill_amount', 'total_consumption')
    def _check_amounts(self):
        for record in self:
            if record.total_bill_amount < 0:
                raise ValidationError("Total bill amount cannot be negative!")
            if record.total_consumption < 0:
                raise ValidationError("Total consumption cannot be negative!")

    @api.constrains('period_covered_from', 'period_covered_to')
    def _check_period(self):
        for record in self:
            if record.period_covered_from and record.period_covered_to:
                if record.period_covered_to < record.period_covered_from:
                    raise ValidationError("Period 'To' date cannot be earlier than 'From' date!")

    @api.constrains('bill_date', 'due_date')
    def _check_dates(self):
        for record in self:
            if record.bill_date and record.due_date:
                if record.due_date < record.bill_date:
                    raise ValidationError("Due date cannot be earlier than bill date!")

    def name_get(self):
        result = []
        # Map utility types to labels (since utility_type is a related field)
        utility_type_map = {
            'electricity': 'Electricity',
            'water': 'Water',
        }
        
        for record in self:
            utility_label = utility_type_map.get(record.utility_type, record.utility_type or 'Unknown')
            bill_date_str = record.bill_date.strftime('%Y-%m-%d') if record.bill_date else 'No Date'
            name = f"{utility_label} Bill - {record.utility_account_number} - {bill_date_str}"
            result.append((record.id, name))
        return result
    
    def _generate_transaction_dates(self, frequency, period_from, period_to):
        """Generate transaction dates based on frequency within the period"""
        dates = []
        current = period_from
        
        if frequency == 'daily':
            # Generate dates for weekdays only (Monday-Friday)
            while current <= period_to:
                if current.weekday() < 5:  # Monday=0 to Friday=4
                    dates.append(current)
                current += timedelta(days=1)
        elif frequency == 'weekly':
            # Generate dates weekly (start on Monday)
            # Find first Monday on or after period_from
            while current.weekday() != 0:  # 0 = Monday
                current += timedelta(days=1)
            while current <= period_to:
                dates.append(current)
                current += timedelta(days=7)
        elif frequency == 'monthly':
            # Generate one date per month within the period
            # Use the first day of each month
            temp_date = period_from.replace(day=1)
            while temp_date <= period_to:
                if temp_date >= period_from:
                    dates.append(temp_date)
                # Move to next month
                if temp_date.month == 12:
                    temp_date = temp_date.replace(year=temp_date.year + 1, month=1)
                else:
                    temp_date = temp_date.replace(month=temp_date.month + 1)
        
        return sorted(dates)
    
    def action_generate_transactions(self):
        """Generate utility transactions for all stalls assigned to this utility account.

        After generation, trigger a client-side reload so the user immediately
        sees the newly created transactions in the One2Many table.
        """
        self.ensure_one()
        
        if not self.utility_account_id:
            raise ValidationError("Utility Account must be set to generate transactions!")
        
        if not self.period_covered_from or not self.period_covered_to:
            raise ValidationError("Period coverage dates must be set to generate transactions!")
        
        # Find all stalls with this utility account
        stalls = self.env['kst.stall'].search([
            ('utility_account_id', '=', self.utility_account_id.id),
            ('is_active', '=', True)
        ])
        
        if not stalls:
            raise ValidationError(f"No active stalls found for utility account {self.utility_account_id.display_name}!")
        
        # Determine which pay type field to use based on utility type
        utility_type = self.utility_type
        if utility_type not in ['electricity', 'water']:
            raise ValidationError("Utility type must be electricity or water!")
        
        # Generate transactions for each stall
        transaction_vals_list = []
        for stall in stalls:
            # Get the pay type based on utility type
            if utility_type == 'electricity':
                pay_type = stall.electric_pay_type_id
            else:  # water
                pay_type = stall.water_pay_type_id
            
            if not pay_type:
                continue  # Skip stalls without pay type for this utility
            
            # Get frequency from pay type
            frequency = pay_type.sub_group
            if not frequency:
                continue  # Skip if no frequency set
            
            # Generate transaction dates based on frequency
            transaction_dates = self._generate_transaction_dates(
                frequency, 
                self.period_covered_from, 
                self.period_covered_to
            )
            
            # Check for existing transactions to avoid duplicates
            existing_dates = self.env['kst.market.utility.transaction'].search([
                ('stall_id', '=', stall.id),
                ('utility_bill_id', '=', self.id),
                ('utility_type', '=', utility_type),
            ]).mapped('transaction_date')
            
            # Create transaction records (incomplete - missing readings, amounts, etc.)
            for trans_date in transaction_dates:
                if trans_date not in existing_dates:
                    transaction_vals_list.append({
                        'stall_id': stall.id,
                        'utility_bill_id': self.id,
                        'transaction_date': trans_date,
                        'utility_type': utility_type,
                        'payment_status': 'pending',
                        # Leave empty: previous_reading, current_reading, consumption, 
                        # applied_rate, amount_paid, receipt_number
                    })
        
        if transaction_vals_list:
            self.env['kst.market.utility.transaction'].create(transaction_vals_list)
        # Whether or not records were created, reload the form so the user sees
        # the current transactions immediately.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

