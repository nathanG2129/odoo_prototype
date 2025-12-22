from odoo import api, fields, models


class Tenant(models.Model):
    _name = 'kst.tenant'
    _description = 'Market Tenant'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    name = fields.Char('Tenant Name', required=True, tracking=True)
    date_started = fields.Date('Date Started', tracking=True)
    date_end = fields.Date('Date End', tracking=True)
    active = fields.Boolean('Active', default=True, compute='_compute_active', store=True)
    
    # One2many relationships
    stall_ids = fields.One2many('kst.stall', 'tenant_id', string='Stalls')
    stall_count = fields.Integer('Number of Stalls', compute='_compute_stall_count')

    @api.depends('date_end')
    def _compute_active(self):
        today = fields.Date.today()
        for record in self:
            if record.date_end:
                record.active = record.date_end >= today
            else:
                record.active = True

    @api.depends('stall_ids')
    def _compute_stall_count(self):
        for record in self:
            record.stall_count = len(record.stall_ids)

