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


class DocuwareDocuments(models.Model):
    _name = "docuware.documents"
    _description = "Documents to work with Odoo and Apps"

    name = fields.Char(string='Name')
    docuware_cabinet_id = fields.Many2one('docuware.cabinets', string='Cabinet')
    #docuware_operations_id = fields.Many2one('docuware.operations', string='Operations')
    docuware_document_guid = fields.Char(string='Cabinet Guid')
    docuware_document_error_log = fields.Text(string="Error log")
    docuware_operation_done = fields.Boolean("Operation Done")
    docuware_json = fields.Text("Server Json")
    docuware_binary = fields.Binary("Original")

    def get_document_data(self):
        c_path = Path('cookies.bin')
        credentials = {'user': self.env.user.company_id.docuware_user,
                       'password': self.env.user.company_id.docuware_pass}
        s = self.docuware_cabinet_id.login(credentials, c_path)

        for document in self:
            try:
                url = f'{self.env.user.company_id.docuware_url}' \
                      f'/docuware/platform/FileCabinets/{document.docuware_cabinet_id.docuware_cabinet_guid}' \
                      f'/Documents/{document.docuware_document_guid}'
                resp = s.request('GET', url)

                if resp.status_code == 200:
                    # return json.loads(resp.content.decode('utf-8'))
                    res = json.loads(resp.content.decode('utf-8'))
                    for i in range(len(res['Fields'])):
                        print(res['Fields'][i]['FieldName'])

            except Exception as e:
                if not document.docuware_document_error_log:
                    document.docuware_document_error_log = str(datetime.now()) + " " + str(e) + "\n"
                else:
                    document.docuware_document_error_log += str(datetime.now()) + " " + str(e) + "\n"

        self.docuware_cabinet_id.logout(c_path, s)

    def generate_attachment(self, s, img_url):
        if img_url:
            url = f'{self.env.user.company_id.docuware_url}' \
                  f'{img_url}'
            response = s.request('GET', url)
            if response.status_code == 200:
                return base64.b64encode(response.content)
        else:
            if not self.docuware_document_error_log:
                self.docuware_document_error_log = str(datetime.now()) + " " + "No document received" + "\n"
            else:
                self.docuware_document_error_log += str(datetime.now()) + " " + "No document received" + "\n"

    def get_document_data_from_operation(self, fields, s):
        try:
            url = f'{self.env.user.company_id.docuware_url}' \
                  f'/docuware/platform/FileCabinets/{self.docuware_cabinet_id.docuware_cabinet_guid}' \
                  f'/Documents/{self.docuware_document_guid}'
            resp = s.request('GET', url)

            if resp.status_code == 200:
                res = json.loads(resp.content.decode('utf-8'))
                mandatory = []
                fdownload = False

                for j in range(len(res['Links'])):
                    print(res['Links'][j]['rel'])
                    if res['Links'][j]['rel'] == "fileDownload":
                        fdownload = res['Links'][j]['href']
                        print(fdownload)
                self.docuware_json = res

                for f in fields:
                    print("FIELD", f.name)
                    for i in range(len(res['Fields'])):
                        #print(res['Links'][i]['rel'])
                        if res['Fields'][i]['FieldName'] == f.name:
                            mandatory.append(f.name)
                            print("Coincide", res['Fields'][i]['FieldName'])
                            print(mandatory)
                if len(mandatory) == len(fields):
                    self.docuware_binary = self.generate_attachment(s, fdownload)

        except Exception as e:
            if not self.docuware_document_error_log:
                self.docuware_document_error_log = str(datetime.now()) + " " + str(e) + "\n"
            else:
                self.docuware_document_error_log += str(datetime.now()) + " " + str(e) + "\n"



