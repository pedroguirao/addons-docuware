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


class DocuwareDictionary(models.Model):
    _name = "docuware.dictionary"
    _description = "Fields to sync by document type"

    name = fields.Char(string='Name')
    line_ids = fields.One2many('docuware.dictionary.line', 'dictionary_id',  string='Lines')
    cabinet_ids = fields.One2many('docuware.cabinet', 'dictionary_id', string='Cabinets',
                                  store='True', readonly=True)