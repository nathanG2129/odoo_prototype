from odoo import fields, models


class ExpenseCategory(models.Model):
    _name = 'kst.expense.category'
    _description = 'Expense Category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    name = fields.Char('Category Name', required=True, tracking=True)



