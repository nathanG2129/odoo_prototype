from odoo import api, fields, models


class UtilityAccount(models.Model):
    _inherit = 'kst.utility.account'
    
    # One2many relationship to stalls (markets module)
    stall_ids = fields.One2many('kst.stall', 'utility_account_id', string='Associated Stalls', readonly=True)
    stall_count = fields.Integer('Stall Count', compute='_compute_stall_count', store=False)
    
    # One2many relationship to utility bills
    utility_bill_ids = fields.One2many('kst.utility.bill', 'utility_account_id', string='Utility Bills', readonly=True)
    utility_bill_count = fields.Integer('Utility Bill Count', compute='_compute_utility_bill_count', store=False)
    
    @api.depends('stall_ids')
    def _compute_stall_count(self):
        for record in self:
            record.stall_count = len(record.stall_ids)
    
    @api.depends('utility_bill_ids')
    def _compute_utility_bill_count(self):
        for record in self:
            record.utility_bill_count = len(record.utility_bill_ids)


