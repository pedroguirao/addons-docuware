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
    _inherit = "docuware.document"

    name = fields.Char(string='Name')
    partner_ids = fields.Many2many('res.partner', string='Signants')

    document_type = fields.Selection(selection_add=[('nomina', 'Nomina')])
    docuware_nomina_done = fields.Boolean(string="Done")
    viafirma_id = fields.Many2one('viafirma', string='Viafirma')

    def get_signants(self):
        if self.env.user.company_id.mandatory_field_ids:
            partners = []
            for field in self.env.user.company_id.mandatory_field_ids:
                doc_field = self.env['docuware.value'].sudo().search(
                                [('name', '=', field.name), ("document_id", "=", self.id)], limit=1)
                if doc_field:
                    partner = self.env['res.partner'].sudo().search([('vat', '=', doc_field.value)], limit=1)
                    partners.append(partner.id)
            if partners:
                self.write({'partner_ids': [(6, 0, partners)]})
            return True
        else:
            return False

    def get_signants_test(self):
        print("GET SIGNANT TEST")
        partners = []
        for field in self.value_ids:
            partner = field.get_value_field_relation()
            if partner:
                partners.append(partner.id)
        if partners:
            self.write({'partner_ids': [(6, 0, partners)]})
            return True
        else:
            return False

    def clip_nomina(self, docid, s):
        if docid:
            try:
                url = f'{self.env.user.company_id.docuware_url}/docuware/platform/FileCabinets/' \
                           f'{self.env.user.company_id.docuware_cabinet_read_id.docuware_cabinet_guid}/' \
                           f'Operations/ClippedDocuments?docId={self.docuware_document_guid}&operation=Clip'

                s.headers.update({'Content-Type': 'application/json'})
                s.headers.update({'Accept': 'application/json'})

                f = {"Int": [docid]}

                index_json = json.dumps(f)

                r = s.request('POST', url, data=index_json, timeout=30)

            except Exception as e:
                if not self.document_error_log:
                    self.document_error_log = str(datetime.now()) + " " + str(e) + "\n"
                    return False
                else:
                    self.document_error_log += str(datetime.now()) + " " + str(e) + "\n"
                    return False

    def upload_and_clip(self, s):
        try:
            file_name = str(self.name) + "_signed"
            url = f'{self.env.user.company_id.docuware_url}/docuware/platform/FileCabinets/' \
                  f'{self.env.user.company_id.docuware_cabinet_read_id.docuware_cabinet_guid}/Documents'

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

            r = s.request('POST', url, files=multipart_form_data, timeout=30)
            res = json.loads(r.content.decode('utf-8'))

            DWDOCID = 0
            for i in range(len(res['Fields'])):
                if res['Fields'][i]['FieldName'] == 'DWDOCID':
                    DWDOCID = res['Fields'][i]['Item']

            if DWDOCID != 0:
                self.clip_nomina(DWDOCID, s)
                return True
            else:
                return False

        except Exception as e:
            if not self.document_error_log:
                self.document_error_log = str(datetime.now()) + " " + str(e) + "\n"
                return False
            else:
                self.document_error_log += str(datetime.now()) + " " + str(e) + "\n"
                return False




