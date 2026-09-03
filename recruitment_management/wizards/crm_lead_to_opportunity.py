from odoo import fields, models


class CrmLead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    email_attach = fields.Binary(
        string='Email Attachment',
        required=True,
        attachment=True,
    )
    email_attach_filename = fields.Char(string='Filename')

    def action_apply(self):
        if self.email_attach:
            # Save attachment to the lead record so it appears on the opportunity
            self.lead_id.write({
                'email_attach': self.email_attach,
                'email_attach_filename': self.email_attach_filename or 'Email Attachment',
            })
        return super().action_apply()
