from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UtilityAccount(models.Model):
    _name = 'kst.utility.account'
    _description = 'Utility Account'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('account_number_unique', 'UNIQUE(utility_account_number)', 'Utility account number must be unique!'),
    ]
    _order = "utility_type, utility_account_number"

    utility_account_number = fields.Char('Utility Account Number', required=True, tracking=True,
                                        help="Account number from utility provider (e.g., MERALCO, Water)")
    utility_type = fields.Selection([
        ('electricity', 'Electricity'),
        ('water', 'Water'),
    ], string='Utility Type', required=True, tracking=True)
    account_name = fields.Char('Account Name', tracking=True,
                              help="Name registered on the account")

    def name_get(self):
        result = []
        for record in self:
            utility_label = dict(self._fields['utility_type'].selection).get(record.utility_type, '')
            name = f"{utility_label} - {record.utility_account_number}"
            if record.account_name:
                name += f" ({record.account_name})"
            result.append((record.id, name))
        return result

