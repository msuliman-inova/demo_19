from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal as PortalController
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request, route

class CustomerPortalUserType(PortalController):
    @route(['/my/account'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def account(self, redirect=None, **post):
        """Override to handle user_type field in portal account"""
        # Handle POST request to update user_type
        if request.httprequest.method == 'POST' and 'user_type' in post:
            partner = request.env.user.partner_id
            user_type = post.get('user_type', 'other')

            if user_type in ['employee', 'employer', 'other']:
                partner.sudo().write({'user_type': user_type})

                # Add employer to Recruitment Management / Portal group
                if user_type == 'employer':
                    group = request.env.ref('recruitment_management.group_recruitment_portal', raise_if_not_found=False)
                    if group and request.env.user.id not in group.users.ids:
                        group.sudo().write({'user_ids': [(4, request.env.user.id)]})

        # Call parent method to get response with proper context
        response = super().account(redirect=redirect, **post)
        return response

    def details_form_validate(self, data, partner_creation=False):
        """Add user_type to validation"""
        error, error_message = super().details_form_validate(data, partner_creation=partner_creation)

        # Validate user_type if provided
        if 'user_type' in data:
            if data['user_type'] not in ['employee', 'employer', 'other']:
                error['user_type'] = 'error'
                error_message.append('Please select a valid user type.')

        return error, error_message


class AuthSignupUserType(AuthSignupHome):
    """Handle user_type during signup"""

    @route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """Override signup to capture and save user_type"""
        # Get user_type from form
        user_type = kw.get('user_type', 'other')

        # Set user_type in context so it's available during user creation
        request.update_context(signup_user_type=user_type)

        # Call parent signup with context
        response = super(AuthSignupUserType, self).web_auth_signup(*args, **kw)

        return response
