# -*- coding: utf-8 -*-

import json
from odoo import http, _
from odoo.http import request
from odoo.addons.website.controllers.form import WebsiteForm
from odoo.addons.website.controllers.main import Website


class WebsiteContactUs(Website):

    @http.route('/contactus', type='http', auth="public", website=True, sitemap=False)
    def contactus(self, **kwargs):
        """Override contact us page to include subject dropdown"""
        # Get all active subjects
        subjects = request.env['contact.subject'].sudo().search([('active', '=', True)], order='sequence, name')

        # Get all countries
        countries = request.env['res.country'].sudo().search([], order='name')

        # Render the page with subjects and countries
        return request.render("website.contactus", {
            'contact_subjects': subjects,
            'countries': countries,
        })


class WebsiteFormContactUs(WebsiteForm):

    def _handle_website_form(self, model_name, **kwargs):
        """Override form handling to process subject_id for contact forms"""
        # If this is the mail.mail model (contact form) and has subject_id
        if model_name == 'mail.mail' and kwargs.get('subject_id'):
            subject_id = kwargs.get('subject_id')

            try:
                subject_id = int(subject_id)
                subject = request.env['contact.subject'].sudo().browse(subject_id)

                if subject.exists():
                    # Create opportunity with subject
                    opportunity_vals = {
                        'contact_name': kwargs.get('name', ''),
                        'email_from': kwargs.get('email_from', ''),
                        'phone': kwargs.get('phone', ''),
                        'partner_name': kwargs.get('company', ''),
                        'description': kwargs.get('description', ''),
                        'type': 'opportunity',
                        'subject_id': subject_id,
                        'name': subject.name,
                        'preferred_contact_method': kwargs.get('preferred_contact_method', False),
                        'best_time_to_contact': kwargs.get('best_time_to_contact', False),
                    }

                    # Add country if provided
                    if kwargs.get('country_id'):
                        try:
                            country_id = int(kwargs.get('country_id'))
                            opportunity_vals['country_id'] = country_id
                        except (ValueError, TypeError):
                            pass

                    lead = request.env['crm.lead'].sudo().create(opportunity_vals)

                    # Set session variables for form builder
                    request.session['form_builder_model_model'] = 'crm.lead'
                    request.session['form_builder_model'] = 'CRM Lead'
                    request.session['form_builder_id'] = lead.id

                    # Return the proper format
                    return json.dumps({'id': lead.id})
            except (ValueError, TypeError):
                pass

        # Fall back to default form handling
        return super(WebsiteFormContactUs, self)._handle_website_form(model_name, **kwargs)
