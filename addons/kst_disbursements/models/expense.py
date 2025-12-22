from odoo import fields, models


class Expense(models.Model):
    _name = 'kst.expense'
    _description = 'Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    category_id = fields.Many2one('kst.expense.category', string='Expense Category', required=True, ondelete='restrict', tracking=True)
    name = fields.Char('Expense Name', required=True, tracking=True)
    expense_type = fields.Char('Expense Type', tracking=True)
    general_group = fields.Char('General Group', tracking=True)



