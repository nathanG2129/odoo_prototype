from odoo import api, fields, models


class Lessee(models.Model):
    _name = 'kst.lessee'
    _description = 'Lessee (Unit Tenant)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    name = fields.Char('Lessee Name', required=True, tracking=True)
    address = fields.Text('Lessee Address', tracking=True)
    contact = fields.Char('Lessee Contact', tracking=True)
    email = fields.Char('Lessee Email', tracking=True)
    
    # One2many relationships
    contract_ids = fields.One2many('kst.contract', 'lessee_id', string='Contracts')
    contract_count = fields.Integer('Number of Contracts', compute='_compute_contract_count')

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for record in self:
            record.contract_count = len(record.contract_ids)


