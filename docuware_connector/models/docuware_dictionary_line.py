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


class DocuwareDictionaryLine(models.Model):
    _name = "docuware.dictionary.line"
    _description = "Lines for document type"

    name = fields.Char(string='Name')
    odoo_field_id = fields.Char(string='Odoo Field')
    required = fields.Boolean(string="Required")
    dictionary_id = fields.Many2one('docuware.dictionary', string='Dictionary')
