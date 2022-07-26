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

class DocuwareValues(models.Model):
    _name = "docuware.value"
    _description = "Fields to sync by document type"

    name = fields.Char(string='Name')
    document_id = fields.Many2one('docuware.document', string='Document')
    odoo_field_id = fields.Char(string='Odoo Field')
    required = fields.Boolean(string="Required")
    value = fields.Char(string='Value')

    def get_value_field_relation(self):
        keys = self.odoo_field_id.split(",")
        if keys:
            object = self.env[keys[0]].sudo().search([(keys[1], '=', self.value)], limit=1)
            if object:
                return object
            else:
                object = self.env[keys[0]].sudo().search([(keys[1], '=', self.value.lower())], limit=1)
                if object:
                    return object
                else:
                    return False