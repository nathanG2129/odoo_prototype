from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta


class UnitUtilityBill(models.Model):
    _name = 'kst.unit.utility.bill'
    _description = 'Unit Utility Bill'
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
    ], string='Collection Status', default='draft', required=True, tracking=True,
       help="Workflow status: Draft > Published > Verified")
    
    # One2many relationship to transactions
    transaction_ids = fields.One2many('kst.unit.utility.transaction', 'utility_bill_id', 
                                     string='Utility Transactions')
    transaction_count = fields.Integer('Transaction Count', compute='_compute_transaction_count')
    has_underpayment = fields.Boolean('Has Underpayment', compute='_compute_has_underpayment', store=False,
                                      help="True when any transaction has amount_paid < amount_due")
    
    # Financial Summary (computed from transactions)
    total_amount_paid = fields.Float('Total Amount Paid', digits=(12, 2), compute='_compute_financial_summary', 
                                    store=False, help="Total amount collected from all transactions")
    profit_loss = fields.Float('Profit & Loss', digits=(12, 2), compute='_compute_financial_summary', 
                               store=False, help="Difference between amount paid and bill amount (Paid - Bill)")
    
    unit_count = fields.Integer('Unit Count', compute='_compute_unit_count', store=False,
                                 help="Number of units assigned to this utility account")

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
    
    @api.depends('utility_account_id', 'utility_type')
    def _compute_unit_count(self):
        for record in self:
            if record.utility_account_id and record.utility_type:
                # Access units through reverse relationship based on utility type
                if record.utility_type == 'electricity':
                    units = self.env['kst.unit'].search([
                        ('electricity_utility_account_id', '=', record.utility_account_id.id),
                    ])
                elif record.utility_type == 'water':
                    units = self.env['kst.unit'].search([
                        ('water_utility_account_id', '=', record.utility_account_id.id),
                    ])
                else:
                    units = self.env['kst.unit']
                record.unit_count = len(units)
            else:
                record.unit_count = 0
    
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
    
    def action_generate_soa(self):
        """Prototype: trigger SOA generation placeholder."""
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
    
    def action_generate_transactions(self):
        """Generate utility transactions for all units assigned to this utility account."""
        self.ensure_one()
        
        if not self.utility_account_id:
            raise ValidationError("Utility Account must be set to generate transactions!")
        
        if not self.period_covered_from or not self.period_covered_to:
            raise ValidationError("Period coverage dates must be set to generate transactions!")
        
        # Find all units with this utility account (based on utility type)
        utility_type = self.utility_type
        if utility_type == 'electricity':
            units = self.env['kst.unit'].search([
                ('electricity_utility_account_id', '=', self.utility_account_id.id),
            ])
        elif utility_type == 'water':
            units = self.env['kst.unit'].search([
                ('water_utility_account_id', '=', self.utility_account_id.id),
            ])
        else:
            units = self.env['kst.unit']
        
        if not units:
            raise ValidationError(f"No units found for utility account {self.utility_account_id.display_name}!")
        
        # Generate one transaction per unit for this billing period
        transaction_vals_list = []
        for unit in units:
            # Check for existing transactions to avoid duplicates
            existing = self.env['kst.unit.utility.transaction'].search([
                ('unit_id', '=', unit.id),
                ('utility_bill_id', '=', self.id),
                ('utility_type', '=', utility_type),
            ])
            
            if not existing:
                transaction_vals_list.append({
                    'unit_id': unit.id,
                    'utility_bill_id': self.id,
                    'transaction_date': self.bill_date,
                    'utility_type': utility_type,
                    # Leave empty: previous_reading, current_reading, consumption, 
                    # applied_rate, amount_paid, receipt_number
                })
        
        if transaction_vals_list:
            self.env['kst.unit.utility.transaction'].create(transaction_vals_list)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

