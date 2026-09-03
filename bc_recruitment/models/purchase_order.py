# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Partner type flags (related fields for easy access in views)
    partner_is_customer = fields.Boolean(string='Partner Is Customer', related='partner_id.is_customer', readonly=True)
    partner_is_agency = fields.Boolean(string='Partner Is Agency', related='partner_id.is_agency', readonly=True)
