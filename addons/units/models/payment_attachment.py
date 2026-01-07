from odoo import api, fields, models


class PaymentAttachmentUnits(models.Model):
    """Extends Payment Attachment with Units-specific transaction links.
    
    This inherits from the base kst.payment.attachment in 'general' module
    and adds Many2one field for unit utility transactions.
    """
    _inherit = 'kst.payment.attachment'
    
    # Reference to unit utility transaction
    unit_utility_transaction_id = fields.Many2one(
        'kst.unit.utility.transaction',
        string='Unit Utility Transaction',
        ondelete='cascade',
        help="Unit utility transaction this attachment belongs to"
    )
    
    # Computed field to show parent transaction (units-specific)
    unit_transaction_reference = fields.Char(
        'Unit Transaction', 
        compute='_compute_unit_transaction_reference', 
        store=False
    )
    
    @api.depends('unit_utility_transaction_id')
    def _compute_unit_transaction_reference(self):
        for record in self:
            if record.unit_utility_transaction_id:
                record.unit_transaction_reference = record.unit_utility_transaction_id.display_name
            else:
                record.unit_transaction_reference = ''

