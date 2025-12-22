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
    total_bill_amount = fields.Float('Total Bill Amount', digits=(12, 2), required=True, tracking=True,
                                     help="Total amount from utility provider")
    derived_rate = fields.Float('Derived Rate', digits=(12, 6), compute='_compute_derived_rate', 
                                store=True, tracking=True,
                                help="Calculated rate per unit (Total Bill / Total Consumption)")
    
    # Related Fields
    utility_type = fields.Selection(related='utility_account_id.utility_type', string='Utility Type', 
                                   store=True, readonly=True)
    utility_account_number = fields.Char(related='utility_account_id.utility_account_number', 
                                        string='Account Number', store=True, readonly=True)
    
    # One2many relationship to transactions
    transaction_ids = fields.One2many('kst.market.utility.transaction', 'utility_bill_id', 
                                     string='Utility Transactions')
    transaction_count = fields.Integer('Transaction Count', compute='_compute_transaction_count')
    
    # Pay Type Information (computed from associated stalls)
    pay_type_summary = fields.Text('Pay Type Summary', compute='_compute_pay_type_summary', store=False,
                                   help="Breakdown of pay types used by stalls in this utility account")
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
    
    @api.depends('utility_account_id', 'utility_type')
    def _compute_pay_type_summary(self):
        """Compute summary of pay types used by stalls in this utility account"""
        for record in self:
            if not record.utility_account_id or not record.utility_type:
                record.pay_type_summary = ''
                continue
            
            # Get all active stalls for this utility account (through reverse relationship)
            stalls = self.env['kst.stall'].search([
                ('utility_account_id', '=', record.utility_account_id.id),
                ('is_active', '=', True)
            ])
            
            # Determine which pay type field to check based on utility type
            if record.utility_type == 'electricity':
                pay_type_field = 'electric_pay_type_id'
            elif record.utility_type == 'water':
                pay_type_field = 'water_pay_type_id'
            else:
                record.pay_type_summary = ''
                continue
            
            # Count stalls by pay type
            pay_type_counts = {}
            for stall in stalls:
                pay_type = getattr(stall, pay_type_field, False)
                if pay_type:
                    pay_type_name = pay_type.display_name or pay_type.code
                    frequency = pay_type.sub_group or 'N/A'
                    key = f"{pay_type_name} ({frequency})"
                    pay_type_counts[key] = pay_type_counts.get(key, 0) + 1
            
            # Format summary
            if pay_type_counts:
                summary_lines = []
                for pay_type_name, count in sorted(pay_type_counts.items()):
                    summary_lines.append(f"• {pay_type_name}: {count} stall(s)")
                record.pay_type_summary = '\n'.join(summary_lines)
            else:
                record.pay_type_summary = 'No pay types assigned to stalls.'

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
        """Generate utility transactions for all stalls assigned to this utility account"""
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
            message = f'Generated {len(transaction_vals_list)} utility transactions for {len(stalls)} stalls.'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Transactions Generated',
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            message = 'All transactions already exist for the selected stalls.'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Transactions Generated',
                    'message': message,
                    'type': 'warning',
                    'sticky': False,
                }
            }

