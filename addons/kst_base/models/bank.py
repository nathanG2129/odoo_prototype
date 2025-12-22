from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Bank(models.Model):
    _name = 'kst.bank'
    _description = 'Bank Account'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('account_number_unique', 'UNIQUE(account_number)', 'Bank account number must be unique!'),
    ]
    _order = "bank_name, account_name"

    bank_name = fields.Char('Bank Name', required=True, tracking=True)
    account_name = fields.Char('Account Name', required=True, tracking=True)
    account_number = fields.Char('Account Number', required=True, tracking=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.bank_name} - {record.account_name} ({record.account_number})"
            result.append((record.id, name))
        return result


