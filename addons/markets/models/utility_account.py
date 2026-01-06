from odoo import api, fields, models


class UtilityAccount(models.Model):
    _inherit = 'kst.utility.account'
    
    # One2many relationships to stalls (markets module) - separate for electricity and water
    electricity_stall_ids = fields.One2many('kst.stall', 'electricity_utility_account_id', 
                                            string='Electricity Stalls', readonly=True)
    water_stall_ids = fields.One2many('kst.stall', 'water_utility_account_id', 
                                      string='Water Stalls', readonly=True)
    stall_count = fields.Integer('Stall Count', compute='_compute_stall_count', store=False)
    
    # One2many relationship to utility bills
    utility_bill_ids = fields.One2many('kst.utility.bill', 'utility_account_id', string='Utility Bills', readonly=True)
    utility_bill_count = fields.Integer('Utility Bill Count', compute='_compute_utility_bill_count', store=False)
    
    @api.depends('electricity_stall_ids', 'water_stall_ids')
    def _compute_stall_count(self):
        for record in self:
            # Count stalls based on utility type
            if record.utility_type == 'electricity':
                record.stall_count = len(record.electricity_stall_ids)
            elif record.utility_type == 'water':
                record.stall_count = len(record.water_stall_ids)
            else:
                record.stall_count = 0
    
    @api.depends('utility_bill_ids')
    def _compute_utility_bill_count(self):
        for record in self:
            record.utility_bill_count = len(record.utility_bill_ids)


