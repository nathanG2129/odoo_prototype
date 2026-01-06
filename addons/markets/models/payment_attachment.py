from odoo import api, fields, models


class PaymentAttachmentMarkets(models.Model):
    """Extends Payment Attachment with Markets-specific transaction links.
    
    This inherits from the base kst.payment.attachment in 'general' module
    and adds Many2one fields for market rent and utility transactions.
    """
    _inherit = 'kst.payment.attachment'
    
    # Reference to parent transactions (only one should be set)
    rent_transaction_id = fields.Many2one(
        'kst.market.rent.transaction',
        string='Rent Transaction',
        ondelete='cascade',
        help="Rent transaction this attachment belongs to"
    )
    utility_transaction_id = fields.Many2one(
        'kst.market.utility.transaction',
        string='Utility Transaction',
        ondelete='cascade',
        help="Utility transaction this attachment belongs to"
    )
    
    # Computed field to show parent transaction (markets-specific)
    market_transaction_reference = fields.Char(
        'Market Transaction', 
        compute='_compute_market_transaction_reference', 
        store=False
    )
    
    @api.depends('rent_transaction_id', 'utility_transaction_id')
    def _compute_market_transaction_reference(self):
        for record in self:
            if record.rent_transaction_id:
                record.market_transaction_reference = record.rent_transaction_id.display_name
            elif record.utility_transaction_id:
                record.market_transaction_reference = record.utility_transaction_id.display_name
            else:
                record.market_transaction_reference = ''

