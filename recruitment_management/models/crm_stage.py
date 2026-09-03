from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_new = fields.Boolean(string='Is New', default=False)
    is_in_progress = fields.Boolean(string='In Progress', default=False)
    is_confirmed = fields.Boolean(string='Is Confirmed', default=False)
    is_completed = fields.Boolean(string='Is Completed', default=False)
    is_lost = fields.Boolean(string='Is Lost', default=False)

    @api.constrains('is_new', 'is_in_progress', 'is_confirmed', 'is_completed', 'is_lost')
    def _check_single_stage_flag(self):
        for stage in self:
            flags = [stage.is_new, stage.is_in_progress, stage.is_confirmed, stage.is_completed, stage.is_lost]
            if sum(bool(f) for f in flags) > 1:
                raise ValidationError(_('Only one stage flag can be checked at a time. Please select only one of: Is New, In Progress, Is Confirmed, Is Completed, Is Lost.'))
