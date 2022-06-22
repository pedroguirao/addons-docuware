# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################
from odoo import api, fields, models, _
import pickle, logging, json
import requests
import base64
from requests.structures import CaseInsensitiveDict
from datetime import datetime, timedelta
from pathlib import Path


class ResPartner(models.Model):
    _inherit = "res.partner"

    document_ids = fields.Many2many('docuware.document', string='Viafirma Documents')

