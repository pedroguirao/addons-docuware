# Copyright
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import json
import requests
from odoo.exceptions import ValidationError
from odoo import fields, models, api


import logging
_logger = logging.getLogger(__name__)


class Viafirma(models.Model):
    _inherit = 'viafirma'

    docuware_operation_id = fields.Many2one('docuware.operations')

