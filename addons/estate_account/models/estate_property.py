from odoo import models


class EstateProperty(models.Model):
    _inherit = 'estate.property'

    def action_sold(self):
        # Create invoice with invoice lines
        self.env['account.move'].create({
            'partner_id': self.buyer_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Commission (6% of selling price)',
                    'quantity': 1,
                    'price_unit': self.selling_price * 0.06,
                }),
                (0, 0, {
                    'name': 'Administrative fees',
                    'quantity': 1,
                    'price_unit': 100.00,
                }),
            ],
        })
        return super().action_sold()