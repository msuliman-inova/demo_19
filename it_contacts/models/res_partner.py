from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _rec_names_search = ['complete_name', 'email', 'ref', 'vat', 'company_registry', 'customer_code', 'supplier_code']

    is_customer = fields.Boolean(string='Customer')
    customer_code = fields.Char(string='Customer Code', readonly=True, copy=False)

    is_supplier = fields.Boolean(string='Supplier')
    supplier_code = fields.Char(string='Supplier Code', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._assign_partner_codes()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if 'is_customer' in vals or 'is_supplier' in vals:
            self._assign_partner_codes()
        return res

    def _assign_partner_codes(self):
        for partner in self:
            code_vals = {}
            if partner.is_customer and not partner.customer_code:
                code_vals['customer_code'] = self.env['ir.sequence'].next_by_code(
                    'it.contacts.customer.code'
                )
            if partner.is_supplier and not partner.supplier_code:
                code_vals['supplier_code'] = self.env['ir.sequence'].next_by_code(
                    'it.contacts.supplier.code'
                )
            if code_vals:
                partner.write(code_vals)
