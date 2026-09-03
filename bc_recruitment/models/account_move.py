# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def button_cancel(self):
        """Override to reset invoiced flag on placements when invoice is cancelled"""
        # Get all placements linked to these invoices before cancellation
        placements = self.env['bc.placement'].search([('invoice_id', 'in', self.ids)])

        # Call super to cancel the invoice
        result = super(AccountMove, self).button_cancel()

        # Reset invoiced flag for linked placements
        if placements:
            placements.write({
                'invoiced': False,
                'invoice_id': False
            })

        return result

    def button_draft(self):
        """Override to reset invoiced flag on placements when invoice is reset to draft"""
        # Get all placements linked to these invoices
        placements = self.env['bc.placement'].search([('invoice_id', 'in', self.ids)])

        # Call super to set to draft
        result = super(AccountMove, self).button_draft()

        # Reset invoiced flag for linked placements
        if placements:
            placements.write({
                'invoiced': False,
                'invoice_id': False
            })

        return result

    def unlink(self):
        """Override to reset invoiced flag on placements when invoice is deleted"""
        # Get all placements linked to these invoices before deletion
        placements = self.env['bc.placement'].search([('invoice_id', 'in', self.ids)])

        # Reset invoiced flag for linked placements
        if placements:
            placements.write({
                'invoiced': False,
                'invoice_id': False
            })

        # Call super to delete the invoice
        return super(AccountMove, self).unlink()
