from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MarketRentBatch(models.Model):
    _name = 'kst.market.rent.batch'
    _description = 'Market Rent Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "collection_date desc, id desc"

    # Grouping: Market + Collection Date + Collection Type
    market_id = fields.Many2one(
        'kst.market',
        string='Market',
        required=True,
        ondelete='restrict',
        tracking=True,
        help="Market for this rent collection batch.",
    )
    collection_date = fields.Date(
        'Collection Date',
        required=True,
        tracking=True,
        help="Date of rent collection for this batch.",
    )
    collection_type = fields.Selection(
        [
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        string='Collection Type',
        required=True,
        tracking=True,
        help="Rent collection type for this batch. Only stalls with matching rent collection type are included.",
    )

    # Workflow status (mirrors utility bill pattern, but simpler for now)
    collection_status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('verified', 'Verified'),
        ],
        string='Collection Status',
        default='draft',
        required=True,
        tracking=True,
        help="Workflow status: Draft > Published > Verified.",
    )

    # One2many to rent transactions
    transaction_ids = fields.One2many(
        'kst.market.rent.transaction',
        'rent_batch_id',
        string='Rent Transactions',
    )
    transaction_count = fields.Integer(
        'Transaction Count',
        compute='_compute_transaction_count',
        store=False,
    )

    # Summary fields
    total_rent_expected = fields.Float(
        'Total Rent Expected',
        digits=(12, 2),
        compute='_compute_totals',
        store=False,
        help="Sum of stall rent for all transactions in this batch (expected amount).",
    )
    total_rent_paid = fields.Float(
        'Total Rent Paid',
        digits=(12, 2),
        compute='_compute_totals',
        store=False,
        help="Total rent actually paid for this batch (sum of rent_paid).",
    )

    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        for record in self:
            record.transaction_count = len(record.transaction_ids)

    @api.depends('transaction_ids', 'transaction_ids.rent_paid', 'transaction_ids.rent')
    def _compute_totals(self):
        for record in self:
            expected = 0.0
            paid = 0.0
            for txn in record.transaction_ids:
                expected += txn.rent or 0.0
                paid += txn.rent_paid or 0.0
            record.total_rent_expected = expected
            record.total_rent_paid = paid

    @api.constrains('collection_date')
    def _check_collection_date(self):
        for record in self:
            if not record.collection_date:
                raise ValidationError("Collection date must be set.")

    def _should_pay_on_date(self, stall, date):
        """Check if stall should pay rent on this specific date based on rent_collection_type.

        This mirrors the legacy behavior:
        - Daily: weekdays (Mon-Fri)
        - Weekly: specific weekday (use Monday for now)
        - Monthly: first day of the month
        """
        if not stall.rent_collection_type:
            return False

        # Daily: weekdays only
        if stall.rent_collection_type == 'daily':
            return date.weekday() < 5  # 0=Mon, 4=Fri

        # Weekly: Mondays (can be adjusted later if needed)
        if stall.rent_collection_type == 'weekly':
            return date.weekday() == 0  # Monday

        # Monthly: first day of the month
        if stall.rent_collection_type == 'monthly':
            return date.day == 1

        return False

    def action_generate_transactions(self):
        """Generate rent transactions for all active stalls in this market
        that match the batch's collection_type and should pay on collection_date.
        """
        self.ensure_one()

        if self.collection_status != 'draft':
            raise ValidationError("You can only generate transactions for batches in Draft status.")

        if not self.market_id:
            raise ValidationError("Market must be set to generate rent transactions.")

        if not self.collection_date:
            raise ValidationError("Collection date must be set to generate rent transactions.")

        # Find all active stalls in market with matching rent_collection_type
        stalls = self.env['kst.stall'].search([
            ('market_id', '=', self.market_id.id),
            ('rent_collection_type', '=', self.collection_type),
            ('is_active', '=', True),
        ])

        if not stalls:
            raise ValidationError(
                f"No active stalls found in market {self.market_id.display_name} "
                f"with rent collection type '{self.collection_type}'."
            )

        RentTransaction = self.env['kst.market.rent.transaction']

        # Avoid duplicates for the same stall + date + batch
        existing_txns = RentTransaction.search([
            ('rent_batch_id', '=', self.id),
            ('transaction_date', '=', self.collection_date),
        ])
        existing_stall_ids = set(existing_txns.mapped('stall_id').ids)

        vals_list = []
        for stall in stalls:
            if stall.id in existing_stall_ids:
                continue

            if not self._should_pay_on_date(stall, self.collection_date):
                continue

            vals_list.append({
                'rent_batch_id': self.id,
                'stall_id': stall.id,
                'transaction_date': self.collection_date,
                'payment_status': 'pending',
                # Financial fields (rent, COBP) will be encoded by cashier
            })

        if vals_list:
            RentTransaction.create(vals_list)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Rent Transactions Generated',
                'message': 'Rent transactions have been generated for eligible stalls.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_publish(self):
        """Publish the batch for collection."""
        self.ensure_one()
        if self.collection_status != 'draft':
            raise ValidationError("Only draft batches can be published.")
        if not self.transaction_ids:
            raise ValidationError("Cannot publish a batch with no transactions.")
        self.collection_status = 'published'
        return True

    def action_verify(self):
        """Verify the batch after collections are encoded."""
        self.ensure_one()
        if self.collection_status != 'published':
            raise ValidationError("Only published batches can be verified.")
        self.collection_status = 'verified'
        return True

    def name_get(self):
        """Format batch name as: Market - Date - Collection Type"""
        result = []
        for record in self:
            # Format market name
            market_name = record.market_id.display_name or record.market_id.code or 'Unknown Market' if record.market_id else 'No Market'
            
            # Format date
            date_str = record.collection_date.strftime('%Y-%m-%d') if record.collection_date else 'No Date'
            
            # Format collection type (capitalize first letter)
            collection_type_map = {
                'daily': 'Daily',
                'weekly': 'Weekly',
                'monthly': 'Monthly',
            }
            type_str = collection_type_map.get(record.collection_type, record.collection_type or 'Unknown')
            
            # Format: "KTC - 2025-01-05 - Daily"
            name = f"{market_name} - {date_str} - {type_str}"
            result.append((record.id, name))
        return result



