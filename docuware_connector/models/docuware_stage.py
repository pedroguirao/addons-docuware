# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################
from odoo import api, fields, models, tools, SUPERUSER_ID, _
import pickle, logging, json
import requests
import base64
from requests.structures import CaseInsensitiveDict
from datetime import datetime, timedelta
from pathlib import Path

class DocuwareStage(models.Model):
    _name = "docuware.stage"
    _order = 'sequence, id'
    _description = 'Docuware Stage'

    name = fields.Char(string='Name')
    sequence = fields.Integer(default=1)
    description = fields.Text(translate=True)



