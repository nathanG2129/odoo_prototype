from odoo import api, fields, models
from odoo.exceptions import ValidationError


class KCode(models.Model):
    _name = 'kst.kcode'
    _description = 'KCode'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'KCode must be unique!'),
    ]
    _order = "code"

    code = fields.Char('Code', required=True, tracking=True, help="General purpose code (e.g., RET, BBH)")

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.code))
        return result


