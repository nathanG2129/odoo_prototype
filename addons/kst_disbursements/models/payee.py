from odoo import fields, models


class Payee(models.Model):
    _name = 'kst.payee'
    _description = 'Payee/Supplier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    name = fields.Char('Payee Name', required=True, tracking=True)
    address = fields.Text('Address', tracking=True)
    tin = fields.Char('TIN', tracking=True, help="Tax Identification Number")



