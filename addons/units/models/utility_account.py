from odoo import api, fields, models


class UtilityAccountUnits(models.Model):
    """Extends Utility Account with Units-specific relationships.
    
    This inherits from the base kst.utility.account in 'general' module
    and adds One2many fields for unit relationships.
    """
    _inherit = 'kst.utility.account'
    
    # One2many relationships to units - separate for electricity and water
    electricity_unit_ids = fields.One2many('kst.unit', 'electricity_utility_account_id', 
                                           string='Electricity Units', readonly=True)
    water_unit_ids = fields.One2many('kst.unit', 'water_utility_account_id', 
                                     string='Water Units', readonly=True)
    unit_count = fields.Integer('Unit Count', compute='_compute_unit_count', store=False)
    
    # One2many relationship to unit utility bills
    unit_utility_bill_ids = fields.One2many('kst.unit.utility.bill', 'utility_account_id', 
                                            string='Unit Utility Bills', readonly=True)
    unit_utility_bill_count = fields.Integer('Unit Utility Bill Count', 
                                             compute='_compute_unit_utility_bill_count', store=False)
    
    @api.depends('electricity_unit_ids', 'water_unit_ids')
    def _compute_unit_count(self):
        for record in self:
            # Count units based on utility type
            if record.utility_type == 'electricity':
                record.unit_count = len(record.electricity_unit_ids)
            elif record.utility_type == 'water':
                record.unit_count = len(record.water_unit_ids)
            else:
                record.unit_count = 0
    
    @api.depends('unit_utility_bill_ids')
    def _compute_unit_utility_bill_count(self):
        for record in self:
            record.unit_utility_bill_count = len(record.unit_utility_bill_ids)

