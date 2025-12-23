from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VoucherHeader(models.Model):
    _name = 'kst.voucher.header'
    _description = 'Voucher Header'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "voucher_date desc, id desc"

    # Foreign Keys
    prefix_id = fields.Many2one('kst.voucher.prefix', string='Voucher Prefix', ondelete='restrict', tracking=True)
    expense_id = fields.Many2one('kst.expense', string='Expense', ondelete='restrict', tracking=True)
    payee_id = fields.Many2one('kst.payee', string='Payee', required=True, ondelete='restrict', tracking=True)
    bank_id = fields.Many2one('kst.bank', string='Bank', ondelete='restrict', tracking=True)
    kcode_id = fields.Many2one('kst.kcode', string='KCode', ondelete='restrict', tracking=True)

    # Voucher Fields
    voucher_number = fields.Char('Voucher Number', required=True, tracking=True)
    voucher_code = fields.Char('Voucher Code', compute='_compute_voucher_code', store=True, tracking=True, help="Prefix + Voucher Number")
    voucher_date = fields.Date('Voucher Date', required=True, default=fields.Date.today, tracking=True)

    # Check Fields
    check_name = fields.Char('Check Name', tracking=True)
    check_date = fields.Date('Check Date', tracking=True)
    check_number = fields.Char('Check Number', tracking=True)
    check_amount = fields.Float('Check Amount', digits=(12, 2), tracking=True)

    # Other Fields
    particulars = fields.Text('Particulars', tracking=True)
    compute = fields.Float('Compute', digits=(12, 2), tracking=True, help="Computed totals")
    remarks = fields.Text('Remarks', tracking=True)
    is_posted = fields.Boolean('Is Posted', default=False, tracking=True, help="Posted vouchers are readonly")
    period_from = fields.Date('Period Covered From', tracking=True)
    period_to = fields.Date('Period Covered To', tracking=True)

    # Relationships
    detail_ids = fields.One2many('kst.voucher.detail', 'voucher_id', string='Voucher Details')
    detail_count = fields.Integer('Number of Details', compute='_compute_detail_count')

    @api.depends('prefix_id', 'voucher_number')
    def _compute_voucher_code(self):
        for record in self:
            if record.prefix_id and record.voucher_number:
                record.voucher_code = f"{record.prefix_id.code}-{record.voucher_number}"
            elif record.voucher_number:
                record.voucher_code = record.voucher_number
            else:
                record.voucher_code = 'New Voucher'

    @api.depends('detail_ids')
    def _compute_detail_count(self):
        for record in self:
            record.detail_count = len(record.detail_ids)

    @api.constrains('period_from', 'period_to')
    def _check_period(self):
        for record in self:
            if record.period_from and record.period_to:
                if record.period_to < record.period_from:
                    raise ValidationError("Period To cannot be earlier than Period From!")

    def name_get(self):
        result = []
        for record in self:
            payee_name = record.payee_id.name if record.payee_id else 'Unknown Payee'
            if record.voucher_code and record.voucher_code != 'New Voucher':
                name = f"[{record.voucher_code}] {payee_name}"
            else:
                name = payee_name
            result.append((record.id, name))
        return result



