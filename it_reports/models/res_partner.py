from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    cheque_count = fields.Integer(compute='_compute_cheque_count')

    @api.depends()
    def _compute_cheque_count(self):
        cheque_data = self.env['account.cheque']._read_group(
            [('partner_id', 'in', self.ids), ('state', '=', 'uncleared')],
            ['partner_id'], ['__count'],
        )
        counts = {partner.id: count for partner, count in cheque_data}
        for partner in self:
            partner.cheque_count = counts.get(partner.id, 0)

    def action_view_cheques(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('it_reports.action_account_cheque')
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def _get_statement_of_accounts_data(self, date_to=None):
        self.ensure_one()
        date_to = fields.Date.from_string(date_to) if date_to else fields.Date.context_today(self)

        move_lines = self.env['account.move.line'].search([
            ('partner_id', '=', self.id),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('parent_state', '=', 'posted'),
            ('amount_residual', '!=', 0),
            ('date', '<=', date_to),
        ], order='date asc, id asc')

        buckets = ['0-30', '31-60', '61-90', '91-120', '121-150', '151-180', '>180']
        bucket_limits = [30, 60, 90, 120, 150, 180]

        rows = []
        totals = {b: 0.0 for b in buckets}
        cumulative = 0.0
        weighted_dso_sum = 0.0
        total_amount = 0.0

        for line in move_lines:
            move = line.move_id
            invoice_date = move.invoice_date or line.date
            age = (date_to - invoice_date).days

            bucket = buckets[-1]
            for limit, label in zip(bucket_limits, buckets):
                if age <= limit:
                    bucket = label
                    break

            amount = line.amount_residual
            cumulative += amount
            totals[bucket] += amount
            weighted_dso_sum += amount * age
            total_amount += amount

            rows.append({
                'invoice_date': invoice_date,
                'invoice_no': move.name,
                'lpo': move.ref or '',
                'bucket': bucket,
                'amount': amount,
                'dso': age,
                'cumulative': cumulative,
            })

        cheques = self.env['account.cheque'].search([
            ('partner_id', '=', self.id),
            ('state', '=', 'uncleared'),
        ])

        return {
            'date_to': date_to,
            'lines': rows,
            'buckets': buckets,
            'totals': totals,
            'total_amount': total_amount,
            'weighted_dso': round(weighted_dso_sum / total_amount) if total_amount else 0,
            'cheques': cheques,
            'cheques_total': sum(cheques.mapped('amount')),
        }
