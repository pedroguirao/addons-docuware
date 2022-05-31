# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################
from odoo import api, fields, models, _
import pickle, logging, json
import requests
from requests.structures import CaseInsensitiveDict
from pathlib import Path

TYPES = [

]

class DocuwareFields(models.Model):
    _name = "docuware.fields"
    _description = "Fields to sync by document type"

    name = fields.Char(string='Name')
    operation_id = fields.Many2one('docuware.operations', string='Operation')
