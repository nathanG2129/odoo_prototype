from odoo import fields, models


class VoucherDetail(models.Model):
    _name = 'kst.voucher.detail'
    _description = 'Voucher Detail'
    _order = "id"

    voucher_id = fields.Many2one('kst.voucher.header', string='Voucher', required=True, ondelete='cascade')
    
    account_number = fields.Char('Account Number')
    account_name = fields.Char('Account Name')
    bill_due = fields.Float('Bill Due', digits=(12, 2))
    pay_due = fields.Float('Pay Due', digits=(12, 2))
    consumption = fields.Float('Consumption', digits=(12, 2))
    remarks = fields.Text('Remarks')
    period_from = fields.Date('Period From')
    period_to = fields.Date('Period To')



