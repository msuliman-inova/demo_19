from odoo import fields, models


class StatementOfAccountsWizard(models.TransientModel):
    _name = 'account.statement.of.accounts.wizard'
    _description = 'Statement of Accounts Wizard'

    partner_id = fields.Many2one('res.partner', required=True)
    date_to = fields.Date(string='Period End Date', required=True, default=fields.Date.context_today)

    def action_print(self):
        self.ensure_one()
        report = self.env.ref('it_reports.action_report_statement_of_accounts')
        return report.report_action(
            self.partner_id,
            data={'date_to': fields.Date.to_string(self.date_to)},
        )
