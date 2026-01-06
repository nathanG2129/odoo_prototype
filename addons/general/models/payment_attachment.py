from odoo import api, fields, models


class PaymentAttachment(models.Model):
    """Payment Attachment - stores receipt images/files for payment transactions.
    
    This is a shared model in the 'general' module that can be used by any module
    that needs to track payment receipts. Common use cases:
    - Bank deposit slips
    - GCash/Maya payment screenshots
    - Cash receipt photos
    - Check images
    - Voucher supporting documents
    
    To use this model in another module:
    1. Add 'general' to your module's depends
    2. Create a Many2one field in your transaction model pointing to this attachment
    3. Or inherit this model and add your own Many2one field to link to your transaction
    
    Example in markets module:
        class PaymentAttachmentMarkets(models.Model):
            _inherit = 'kst.payment.attachment'
            rent_transaction_id = fields.Many2one('kst.market.rent.transaction', ...)
    """
    _name = 'kst.payment.attachment'
    _description = 'Payment Attachment'
    _order = 'create_date desc'
    
    name = fields.Char('Description', required=True, 
                       help="Brief description of the attachment (e.g., 'GCash Receipt', 'Bank Deposit Slip')")
    
    # File attachment using Odoo's built-in Binary field
    attachment_file = fields.Binary('File', required=True, attachment=True)
    attachment_filename = fields.Char('Filename')
    
    # Payment method for categorization
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Deposit'),
        ('check', 'Check'),
        ('gcash', 'GCash'),
        ('maya', 'Maya'),
        ('other', 'Other'),
    ], string='Payment Method', default='cash', required=True,
       help="Method of payment for this receipt")
    
    # Optional notes
    notes = fields.Text('Notes', help="Additional notes about this attachment")
    
    def name_get(self):
        result = []
        for record in self:
            method_label = dict(record._fields['payment_method'].selection).get(
                record.payment_method, record.payment_method
            )
            name = f"{record.name} ({method_label})"
            result.append((record.id, name))
        return result

