from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta


class Stall(models.Model):
    _name = 'kst.stall'
    _description = 'Market Stall'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "market_id, code"

    # Foreign Keys
    market_id = fields.Many2one('kst.market', string='Market', required=True, ondelete='restrict', tracking=True)
    tenant_id = fields.Many2one('kst.tenant', string='Tenant', ondelete='restrict', tracking=True)
    utility_account_id = fields.Many2one('kst.utility.account', string='Utility Account', 
                                        ondelete='restrict', tracking=True,
                                        help="Utility account that groups stalls under one billing account")
    electric_pay_type_id = fields.Many2one('kst.market.pay.type', string='Electric Pay Type',
                                           domain=[('pay_type_use', 'in', ['electricity', 'both'])], tracking=True)
    water_pay_type_id = fields.Many2one('kst.market.pay.type', string='Water Pay Type',
                                        domain=[('pay_type_use', 'in', ['water', 'both'])], tracking=True)
    
    # Basic Fields
    code = fields.Char('Stall Code', required=True, tracking=True)
    rental_rate = fields.Float('Rental Rate', digits=(12, 2), tracking=True)
    default_electricity_rate = fields.Float('Default Electricity Rate', digits=(12, 2), tracking=True,
                                           help="Flat rate used when not metered")
    default_water_rate = fields.Float('Default Water Rate', digits=(12, 2), tracking=True,
                                     help="Flat rate used when not metered")
    rent_collection_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Rent Collection Type', default='monthly', tracking=True)
    is_active = fields.Boolean('Active', default=True, tracking=True)
    need_or = fields.Boolean('Need OR', default=False, help="Needs Official Receipt", tracking=True)
    
    # Utility Information
    meralco_account_number = fields.Char('Meralco Account Number', tracking=True)
    electricity_sub_meter_number = fields.Char('Electricity Sub-Meter Number', tracking=True)
    
    # Computed Fields
    display_name = fields.Char('Display Name', compute='_compute_display_name', store=True)
    
    # One2many relationships
    rent_transaction_ids = fields.One2many('kst.market.rent.transaction', 'stall_id', string='Rent Transactions')
    utility_transaction_ids = fields.One2many('kst.market.utility.transaction', 'stall_id', string='Utility Transactions')
    
    # Payment Ledger (confirmed/paid transactions)
    ledger_transaction_ids = fields.One2many('kst.market.rent.transaction', 'stall_id', 
                                             string='Payment Ledger', 
                                             domain=[('payment_status', 'in', ['paid', 'partial'])],
                                             readonly=True)
    
    # Computed fields for payment summary
    total_paid = fields.Float('Total Paid', compute='_compute_payment_summary', store=False)
    total_copb_due = fields.Float('Total COPB Due', compute='_compute_payment_summary', store=False)
    last_payment_date = fields.Date('Last Payment Date', compute='_compute_payment_summary', store=False)
    next_payment_date = fields.Date('Next Payment Date', compute='_compute_next_payment_date', store=False)
    ledger_count = fields.Integer('Ledger Count', compute='_compute_ledger_count', store=False)
    
    # Scheduled Payments (One2many to transient model)
    scheduled_payment_ids = fields.One2many('kst.stall.scheduled.payment', 'stall_id', 
                                           string='Scheduled Payments', 
                                           readonly=True)

    @api.depends('market_id', 'code')
    def _compute_display_name(self):
        for record in self:
            if record.market_id and record.code:
                record.display_name = f"[{record.market_id.code}] {record.code}"
            elif record.code:
                record.display_name = record.code
            else:
                record.display_name = 'New Stall'

    @api.constrains('code', 'market_id')
    def _check_code_unique_per_market(self):
        for record in self:
            if record.code and record.market_id:
                existing = self.search([
                    ('code', '=', record.code),
                    ('market_id', '=', record.market_id.id),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(f"Stall code '{record.code}' already exists in market '{record.market_id.name}'!")

    @api.depends('rent_transaction_ids', 'rent_transaction_ids.payment_status', 
                 'rent_transaction_ids.rent_paid', 'rent_transaction_ids.copb_due',
                 'rent_transaction_ids.transaction_date')
    def _compute_payment_summary(self):
        for record in self:
            paid_transactions = record.rent_transaction_ids.filtered(
                lambda t: t.payment_status in ['paid', 'partial']
            )
            record.total_paid = sum(paid_transactions.mapped('rent_paid'))
            
            # Get latest COPB Due from most recent transaction
            if record.rent_transaction_ids:
                latest_trans = record.rent_transaction_ids.sorted('transaction_date', reverse=True)[0]
                record.total_copb_due = latest_trans.copb_due
            else:
                record.total_copb_due = 0.0
            
            # Get last payment date
            if paid_transactions:
                record.last_payment_date = max(paid_transactions.mapped('transaction_date'))
            else:
                record.last_payment_date = False
    
    @api.depends('ledger_transaction_ids')
    def _compute_ledger_count(self):
        for record in self:
            record.ledger_count = len(record.ledger_transaction_ids)
    
    @api.depends('rent_collection_type', 'rent_transaction_ids.transaction_date', 'is_active')
    def _compute_next_payment_date(self):
        today = fields.Date.today()
        for record in self:
            if not record.is_active or not record.rent_collection_type:
                record.next_payment_date = False
                continue
            
            # Get last transaction date
            if record.rent_transaction_ids:
                last_date = max(record.rent_transaction_ids.mapped('transaction_date'))
            else:
                # If no transactions, start from today
                last_date = today
            
            # Calculate next payment date based on collection type
            if record.rent_collection_type == 'daily':
                # Next weekday (skip weekends)
                next_date = last_date + timedelta(days=1)
                while next_date.weekday() >= 5:  # Saturday=5, Sunday=6
                    next_date += timedelta(days=1)
                record.next_payment_date = next_date
            elif record.rent_collection_type == 'weekly':
                # Next week (same day of week)
                record.next_payment_date = last_date + timedelta(days=7)
            else:  # monthly
                # Next month - add 32 days then set to first of that month, then add the day
                # This handles month-end edge cases
                year = last_date.year
                month = last_date.month
                day = last_date.day
                if month == 12:
                    next_year = year + 1
                    next_month = 1
                else:
                    next_year = year
                    next_month = month + 1
                # Try to create the date, if it fails (e.g., Jan 31 -> Feb), use last day of month
                try:
                    record.next_payment_date = fields.Date.to_date(f"{next_year}-{next_month:02d}-{day:02d}")
                except:
                    # Get last day of next month
                    if next_month == 12:
                        last_day_month = fields.Date.to_date(f"{next_year+1}-01-01") - timedelta(days=1)
                    else:
                        last_day_month = fields.Date.to_date(f"{next_year}-{next_month+1:02d}-01") - timedelta(days=1)
                    record.next_payment_date = last_day_month
            
            # If next payment date is in the past, calculate from today
            if record.next_payment_date and record.next_payment_date < today:
                if record.rent_collection_type == 'daily':
                    next_date = today + timedelta(days=1)
                    while next_date.weekday() >= 5:
                        next_date += timedelta(days=1)
                    record.next_payment_date = next_date
                elif record.rent_collection_type == 'weekly':
                    record.next_payment_date = today + timedelta(days=7)
                else:  # monthly
                    year = today.year
                    month = today.month
                    day = today.day
                    if month == 12:
                        next_year = year + 1
                        next_month = 1
                    else:
                        next_year = year
                        next_month = month + 1
                    try:
                        record.next_payment_date = fields.Date.to_date(f"{next_year}-{next_month:02d}-{day:02d}")
                    except:
                        if next_month == 12:
                            last_day_month = fields.Date.to_date(f"{next_year+1}-01-01") - timedelta(days=1)
                        else:
                            last_day_month = fields.Date.to_date(f"{next_year}-{next_month+1:02d}-01") - timedelta(days=1)
                        record.next_payment_date = last_day_month

    
    def _generate_scheduled_payments(self):
        """Generate scheduled payment records for the next 12 payment periods"""
        ScheduledPayment = self.env['kst.stall.scheduled.payment']
        today = fields.Date.today()
        
        for record in self:
            # Clear existing scheduled payments for this stall
            existing = ScheduledPayment.search([('stall_id', '=', record.id)])
            existing.unlink()
            
            if not record.is_active or not record.rent_collection_type or not record.rental_rate:
                continue
            
            # Determine starting date
            if record.next_payment_date and record.next_payment_date >= today:
                start_date = record.next_payment_date
            elif record.rent_transaction_ids:
                # Calculate from last transaction
                last_date = max(record.rent_transaction_ids.mapped('transaction_date'))
                start_date = self._calculate_next_payment_date(last_date, record.rent_collection_type)
            else:
                # No transactions, start from today
                start_date = self._calculate_next_payment_date(today, record.rent_collection_type)
            
            # Generate next 12 scheduled payments
            scheduled_payments = []
            current_date = start_date
            num_payments = 12
            
            for i in range(num_payments):
                if current_date < today:
                    current_date = self._calculate_next_payment_date(today, record.rent_collection_type)
                
                scheduled_payments.append({
                    'stall_id': record.id,
                    'scheduled_date': current_date,
                    'expected_amount': record.rental_rate,
                    'rent_collection_type': record.rent_collection_type,
                    'status': 'Pending',
                })
                
                # Calculate next payment date
                current_date = self._calculate_next_payment_date(current_date, record.rent_collection_type)
            
            # Create the records
            if scheduled_payments:
                ScheduledPayment.create(scheduled_payments)
    
    def action_generate_scheduled_payments(self):
        """Button action to manually regenerate scheduled payments"""
        self._generate_scheduled_payments()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Scheduled Payments',
                'message': 'Scheduled payments have been generated.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _calculate_next_payment_date(self, from_date, collection_type):
        """Helper method to calculate next payment date from a given date"""
        if collection_type == 'daily':
            # Next weekday (skip weekends)
            next_date = from_date + timedelta(days=1)
            while next_date.weekday() >= 5:  # Saturday=5, Sunday=6
                next_date += timedelta(days=1)
            return next_date
        elif collection_type == 'weekly':
            # Next week (same day of week)
            return from_date + timedelta(days=7)
        else:  # monthly
            # Next month
            year = from_date.year
            month = from_date.month
            day = from_date.day
            if month == 12:
                next_year = year + 1
                next_month = 1
            else:
                next_year = year
                next_month = month + 1
            # Try to create the date, if it fails (e.g., Jan 31 -> Feb), use last day of month
            try:
                return fields.Date.to_date(f"{next_year}-{next_month:02d}-{day:02d}")
            except:
                # Get last day of next month
                if next_month == 12:
                    last_day_month = fields.Date.to_date(f"{next_year+1}-01-01") - timedelta(days=1)
                else:
                    last_day_month = fields.Date.to_date(f"{next_year}-{next_month+1:02d}-01") - timedelta(days=1)
                return last_day_month

    def name_get(self):
        result = []
        for record in self:
            if record.market_id:
                name = f"[{record.market_id.code}] {record.code}"
            else:
                name = record.code or 'New Stall'
            result.append((record.id, name))
        return result
    
    def action_view_ledger(self):
        """Action to view payment ledger"""
        self.ensure_one()
        return {
            'name': 'Payment Ledger',
            'type': 'ir.actions.act_window',
            'res_model': 'kst.market.rent.transaction',
            'view_mode': 'tree,form',
            'domain': [('stall_id', '=', self.id), ('payment_status', 'in', ['paid', 'partial'])],
            'context': {'default_stall_id': self.id, 'search_default_paid': 1},
        }
    

