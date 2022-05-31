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

class DocuwareOperations(models.Model):
    _name = "docuware.operations"
    _description = "Methods to connect , upload and download documents"

    name = fields.Char(string='Name')
    document_type = fields.Selection(selection=TYPES, string='Document type')
    docuware_cabinet_read_id = fields.Many2one('docuware.cabinets', string='Download Cabinet')
    docuware_cabinet_write_id = fields.Many2one('docuware.cabinets', string='Upload Cabinet')
    field_ids = fields.One2many('docuware.fields','operation_id', string='Fields')

    def do_operation(self):
        c_path = Path('cookies.bin')
        s = self.docuware_cabinet_read_id.login(c_path)

        for document in self.docuware_cabinet_read_id.docuware_cabinet_document_ids:
            if document.docuware_operation_done:
                print("Not done")
                print(document.name)
                document.get_document_data_from_operation(self.field_ids, s)

        self.docuware_cabinet_read_id.logout(c_path, s)
