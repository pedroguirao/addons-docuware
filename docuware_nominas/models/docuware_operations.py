# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################
from odoo import api, fields, models, _
import pickle, logging, json
import requests
from datetime import datetime
import base64
from requests.structures import CaseInsensitiveDict
from pathlib import Path


class DocuwareOperations(models.Model):
    _inherit = "docuware.operations"





