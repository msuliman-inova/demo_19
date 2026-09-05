from odoo import fields, models


class AccountCheque(models.Model):
    _name = 'account.cheque'
    _description = 'Post-Dated Cheque'
    _order = 'promise_date, id'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    move_id = fields.Many2one(
        'account.move', string='Invoice',
        domain="[('partner_id', '=', partner_id), ('move_type', '=', 'out_invoice')]",
    )
    document_number = fields.Char(string='Document #')
    bank_id = fields.Many2one('res.bank', string='Cheque Drawn On')
    cheque_number = fields.Char(string='Cheque No.')
    cheque_date = fields.Date(string='Actual Cheque Date', required=True)
    promise_date = fields.Date(string='Promise Date', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(required=True)
    state = fields.Selection(
        selection=[('uncleared', 'Uncleared'), ('cleared', 'Cleared'), ('bounced', 'Bounced')],
        default='uncleared', required=True,
    )
    note = fields.Char()
