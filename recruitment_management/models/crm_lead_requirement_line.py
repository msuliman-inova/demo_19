from odoo import api, fields, models


class CrmLeadRequirementLine(models.Model):
    _name = 'crm.lead.requirement.line'
    _description = 'CRM Lead Requirement Line'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        required=True,
        ondelete='cascade',
    )

    product_id = fields.Many2one(
        'product.product',
        string='Service',
        required=True,
    )

    description = fields.Text(
        string='Description',
    )

    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
    )

    price_unit = fields.Float(
        string='Unit Price',
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.price_unit = self.product_id.lst_price
