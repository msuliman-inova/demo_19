# Recruitment Management Module

## Overview
Complete recruitment request management system for Odoo 19 that integrates CRM, HR Recruitment, Sales, and Accounting modules.

## Features

### Core Functionality
- **Employer Portal**: Self-service portal for employers to submit recruitment requests
- **CRM Integration**: Automatic lead creation for each recruitment request
- **Dynamic Pricing**: Configurable pricing rules based on contract type and experience level
- **Quotation Management**: Generate and send quotations to employers
- **Sales Integration**: Automatic sales order creation upon approval
- **Job Position Creation**: Convert approved requests to job positions in HR Recruitment
- **Invoice Integration**: Track invoices related to recruitment services

### Workflow
1. **Draft**: Employer creates recruitment request via portal
2. **Submitted**: Request submitted and CRM lead created automatically
3. **Under Review**: Recruitment team reviews the request
4. **Quotation Sent**: Quotation with pricing sent to employer
5. **Approved**: Employer approves quotation, sales order created
6. **In Progress**: Job position created, recruitment process starts
7. **Completed**: Position filled successfully

### User Roles
- **Portal User (Employer)**: Submit and track recruitment requests
- **Recruitment Officer**: Manage requests, send quotations, create jobs
- **Recruitment Manager**: Full access including pricing configuration and approvals

## Installation

1. Copy the `recruitment_management` folder to your Odoo addons directory
2. Update the apps list: Settings → Apps → Update Apps List
3. Search for "Recruitment Management"
4. Click Install

## Configuration

### Initial Setup
1. Navigate to **Recruitment Management → Configuration → Pricing Rules**
2. Review and adjust the default pricing rules
3. Configure additional services in **Configuration → Additional Services**

### Employer Setup
1. Create or update partner records for employer companies
2. Mark partners as employers: Check "Is Employer" field
3. Create portal users for employers
4. Assign them to the "Portal - Employer" group

### Email Templates
The module includes default email templates for:
- Request submission confirmation
- Quotation sending
- Approval notification

Customize these in Settings → Technical → Email Templates

## Usage

### For Employers (Portal Users)
1. Log in to the portal
2. Go to "Recruitment Requests"
3. Click "New Request"
4. Fill in job details and requirements
5. Submit or save as draft
6. Track request status and receive notifications

### For Recruitment Officers
1. View submitted requests in Recruitment Management
2. Review request details
3. Send quotation using the "Send Quotation" button
4. Upon approval, create sales order
5. Convert to job position to start recruiting
6. Manage applicants in HR Recruitment module

### For Managers
- Access all requests and configure system settings
- Review and approve quotations
- Manage pricing rules and additional services
- Generate reports and analytics

## Technical Details

### Dependencies
- base
- crm
- hr_recruitment
- portal
- sale_management
- account
- mail
- web

### Main Models
- `recruitment.request`: Main recruitment request model
- `recruitment.pricing`: Pricing configuration
- `recruitment.additional.service`: Additional services catalog

### Security
- Multi-level access control with three user groups
- Record rules for data isolation
- Portal users can only see their own requests

## Customization

### Adding Custom Fields
Edit `models/recruitment_request.py` and add fields to the RecruitmentRequest class.

### Modifying Workflow
Adjust the `state` selection field and related action methods in the model.

### Portal Customization
Templates are in `views/portal_recruitment_request_templates.xml`

### Pricing Logic
Modify the `_compute_service_fee` method in `recruitment_request.py` to change pricing calculation.

## Support

For support, please contact: support@haidabsmart.com

## License

LGPL-3

## Credits

Developed by the Recruitment Suite Team

## Changelog

### Version 19.0.1.0.0
- Initial release for Odoo 19
- Complete workflow from request to hire
- Portal integration
- CRM, Sales, and Accounting integration
- Dynamic pricing system
- Multi-language support ready