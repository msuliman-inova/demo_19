# Job Seeker Registration Module

## Overview
This module allows job seekers to register their interest when no suitable positions are currently available. HR managers can then contact them when matching positions become available and convert their registration to job applications with a single click.

## Features

### For Job Seekers (Website)
- **Registration Button**: A prominent button on the /jobs page for job seekers who can't find suitable positions
- **Registration Form**: Modal form collecting:
  - Personal information (name, email, phone, mobile)
  - Desired position and department
  - Experience years and expected salary
  - Available from date
  - Education level
  - Resume/CV upload
  - Cover letter
- **Thank You Page**: Confirmation page after successful registration

### For HR Managers (Backend)
- **Job Seeker Pool**: Centralized view of all registrations under Recruitment menu
- **Status Tracking**:
  - New
  - Contacted
  - Still Interested
  - Not Interested
  - Converted to Application
  - Archived
- **One-Click Conversion**: Convert any registration to a job application instantly
- **Smart Matching**: Automatically searches for matching job positions during conversion
- **Resume Attachment**: Resumes are automatically attached to job applications
- **Activity Tracking**: Full chatter support for notes and communication history

## Installation

1. Place this module in your Odoo addons directory
2. Update the apps list: `Apps > Update Apps List`
3. Search for "Job Seeker Registration"
4. Click Install

## Usage

### Job Seeker Registration Flow
1. Job seeker visits `/jobs` page
2. Clicks "Register Your Interest" button
3. Fills in the registration form
4. Submits and receives confirmation

### HR Manager Workflow
1. Go to `Recruitment > Job Seeker Pool`
2. Review new registrations
3. Contact interested candidates
4. When a matching position becomes available:
   - Open the registration
   - Click "Convert to Application"
   - The system creates a job application with all data
   - Resume is automatically attached
5. Continue with normal recruitment process

## Technical Details

### Models
- `job.seeker.registration`: Main model for storing job seeker data

### Controllers
- `/jobs`: Extended to include departments and degrees
- `/job-seeker/register`: Handles form submission
- `/job-seeker/thank-you`: Thank you page

### Key Actions
- `action_convert_to_application()`: Converts registration to hr.applicant
- `action_contact_seeker()`: Marks registration as contacted
- `action_mark_interested()`: Marks as still interested
- `action_mark_not_interested()`: Marks as not interested

## Dependencies
- base
- hr_recruitment
- website
- mail

## Version
19.0.1.0.0

## Author
Haidab Smart Solution

## License
LGPL-3
