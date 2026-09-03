# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ContactSubject(models.Model):
    _name = 'contact.subject'
    _description = 'Contact Us Subject'
    _order = 'sequence, name'

    name = fields.Char(string='Subject', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    _name_unique = models.Constraint(
        'unique(name)',
        'Subject name must be unique!'
    )
