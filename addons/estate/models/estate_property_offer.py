from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError

class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'
    _sql_constraints = [
        ('check_price', 'CHECK(price > 0)', 'The offer price must be strictly positive.'),
    ]
    _order = "price desc"

    price = fields.Float('Price')
    status = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ], copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    property_id = fields.Many2one('estate.property', string='Property', required=True)
    property_type_id = fields.Many2one('estate.property.type', string='Property Type', related='property_id.property_type_id', store=True)
    validity = fields.Integer('Validity (days)', default=7)
    date_deadline = fields.Date('Deadline', compute='_compute_date_deadline', inverse='_inverse_date_deadline')

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for record in self:
            if record.create_date:
                record.date_deadline = record.create_date.date() + timedelta(days=record.validity)
            else:
                record.date_deadline = fields.Date.today() + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if record.create_date:
                record.validity = (record.date_deadline - record.create_date.date()).days
            else:
                record.validity = (record.date_deadline - fields.Date.today()).days

    def action_accept(self):
        for record in self:
            # Set the offer status to accepted
            record.status = 'accepted'
            # Set the buyer and selling price on the property
            record.property_id.buyer_id = record.partner_id
            record.property_id.selling_price = record.price
        return True

    def action_refuse(self):
        for record in self:
            record.status = 'refused'
        return True

    @api.model
    def create(self, vals):
        # Get the property
        property_id = vals.get('property_id')
        if property_id:
            property_obj = self.env['estate.property'].browse(property_id)
            
            # Check if new offer price is higher than existing offers
            if property_obj.offer_ids:
                max_existing_price = max(property_obj.offer_ids.mapped('price'))
                if vals.get('price', 0) <= max_existing_price:
                    raise UserError(
                        'The offer price must be higher than existing offers. '
                        'Current highest offer: %.2f' % max_existing_price
                    )
            
            # Set property state to 'Offer Received'
            property_obj.state = 'offer_received'
        
        # Call parent create method
        return super().create(vals)