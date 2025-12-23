from odoo import api, fields, models
from datetime import timedelta


class StallScheduledPayment(models.TransientModel):
    """Transient model to display scheduled future payments for a stall"""
    _name = 'kst.stall.scheduled.payment'
    _description = 'Stall Scheduled Payment'
    _order = 'scheduled_date'

    stall_id = fields.Many2one('kst.stall', string='Stall', required=True, ondelete='cascade')
    scheduled_date = fields.Date('Scheduled Date', required=True)
    expected_amount = fields.Float('Expected Amount', digits=(12, 2), required=True)
    rent_collection_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Collection Type', required=True)
    status = fields.Char('Status', default='Pending', readonly=True)

    def name_get(self):
        result = []
        for record in self:
            date_str = record.scheduled_date.strftime('%Y-%m-%d') if record.scheduled_date else 'No Date'
            name = f"{date_str} - ₱{record.expected_amount:,.2f}"
            result.append((record.id, name))
        return result

