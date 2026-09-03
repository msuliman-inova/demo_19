from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    user_type = fields.Selection(
        related='partner_id.user_type',
        string='User Type',
        readonly=False,
        store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Get user_type from context and set on partner during user creation"""
        # Get user_type from context if available
        context_user_type = self.env.context.get('signup_user_type')

        users = super().create(vals_list)

        # Set user_type on partner after creation
        for user, vals in zip(users, vals_list):
            user_type = vals.get('user_type') or context_user_type

            if user_type and user.partner_id:
                user.partner_id.sudo().write({'user_type': user_type})

        return users