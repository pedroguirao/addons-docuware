# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################
from odoo import api, fields, models, tools, SUPERUSER_ID, _
import pickle, logging, json
import requests
from requests.structures import CaseInsensitiveDict
import base64
from requests.structures import CaseInsensitiveDict
from datetime import datetime, timedelta
from pathlib import Path


class DocuwareNominas(models.Model):
    _inherit = "docuware.documents"

    name = fields.Char(string='Name')
    partner_ids = fields.Many2many('res.partner', string='Signants')

    document_type = fields.Selection(selection_add=[('nomina', 'Nomina')])
    docuware_nomina_done = fields.Boolean(string="Done")
    viafirma_id = fields.Many2one('viafirma', string='Viafirma')

    def get_signants(self):
        if self.env.user.company_id.viafirma_fields:
            partners = []
            for field in self.env.user.company_id.viafirma_fields:
                print("DEBUG SIGNANTS", field.name)
                doc_field = self.env['docuware.fields'].sudo().search(
                                [('name', '=', field.name), ("document_id", "=", self.id)], limit=1)
                print("DEBUG SIGNANTS doc value", doc_field.value)
                if doc_field:
                    partner = self.env['res.partner'].sudo().search([('vat', '=', doc_field.value)], limit=1)
                    print("PARTNER", partner.name)
                    partners.append(partner.id)
                    print("PARTNERS", partners)
            if partners:
                self.write({'partner_ids': [(6, 0, partners)]})
            return True
        else:
            return False

    #TOCLIP and Staple
    def TOCLIP(self):

        try:
            url = f'{self.env.user.company_id.docuware_url}/docuware/platform/FileCabinets/' \
                       f'{self.env.user.company_id.docuware_cabinet_write_id.docuware_cabinet_guid}/' \
                       f'Operations/ClippedDocuments?docId=1529&operation=Clip'

            print("IN TRY")
            c_path = Path('cookies.bin')
            s = self.docuware_cabinet_id.login(c_path)
            s.headers.update({'Content-Type': 'application/json'})
            s.headers.update({'Accept': 'application/json'})
            print("LOGGED")

            f = {"Int":[1530]}

            index_json = json.dumps(f)
            multipart_form_data = {
                'data': (None, index_json, 'application/json'),
            }

            print("BEFORE POST")
            r = s.request('POST', url, data=index_json, timeout=30)
            print("RESULT", r.json())

        except Exception as e:
            if not self.docuware_document_error_log:
                self.docuware_document_error_log = str(datetime.now()) + " " + str(e) + "\n"
                return False
            else:
                self.docuware_document_error_log += str(datetime.now()) + " " + str(e) + "\n"
                return False

    def upload(self):
        try:
            print("IN TRY")
            c_path = Path('cookies.bin')
            s = self.docuware_cabinet_id.login(c_path)
            print("LOGGED")
            file_name = str(self.name) + "_signed6"
            url = f'{self.env.user.company_id.docuware_url}/docuware/platform/FileCabinets/' \
                  f'{self.env.user.company_id.docuware_cabinet_write_id.docuware_cabinet_guid}/Documents'
            print("URL")
            f = [
                {
                        'FieldName': "ESTADO",
                        'Item': "Nuevo",
                        'ItemElementName': 'String',
                    }
            ]
            #for key, value in fields.items():
            #    f.append({
            #        'FieldName': key,
            #        'Item': value,
            #        'ItemElementName': 'String',
            #    })

            index_json = '{"Fields": ' + json.dumps(f) + '}'
            binary = base64.decodebytes(self.viafirma_id.document_signed)
            multipart_form_data = {
                'document': (None, index_json, 'application/json'),
                'file[]': (str(file_name), binary, 'application/pdf'),
            }
            print("BEFORE POST")
            r = s.request('POST', url, files=multipart_form_data, timeout=30)
            print("HASTA AQUI")



        except Exception as e:
            if not self.docuware_document_error_log:
                self.docuware_document_error_log = str(datetime.now()) + " " + str(e) + "\n"
                return False
            else:
                self.docuware_document_error_log += str(datetime.now()) + " " + str(e) + "\n"
                return False




