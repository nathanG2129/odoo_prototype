from odoo import fields, models


class VoucherPrefix(models.Model):
    _name = 'kst.voucher.prefix'
    _description = 'Voucher Prefix'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Voucher Prefix code must be unique!'),
    ]
    _order = "code"

    code = fields.Char('Prefix Code', required=True, tracking=True, help="e.g., BBHCV, KSTCV")
    name = fields.Char('Prefix Name', tracking=True)
    address = fields.Text('Company Address', tracking=True)



