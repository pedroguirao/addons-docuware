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
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

TYPES = [
]


class DocuwareCabinet(models.Model):
    _name = "docuware.cabinet"
    _description = "Cabinets to connect with Odoo and Apps"

    #name = fields.Char(string='Name')
    type = fields.Selection(
        selection=TYPES,
    )

    name = fields.Char(string='Cabinet')
    guid = fields.Char(string='Cabinet Guid')
    #cabinet_document_ids = fields.One2many('docuware.document','cabinet_id', string='Documents')
    #REVISAR
    cabinet_error_log = fields.Text(string='Error log')

    user_ids = fields.Many2many('res.users', string='Users')

    document_count = fields.Integer(string='Docs', compute='get_docs_count')

    def get_docs_count(self):
        docs = self.env['docuware.document'].search([('cabinet_id', '=', self.id)])
        self.document_count = docs

    def login(self, c_path):
        # Session will hold the cookies
        credentials = {'user': self.env.user.company_id.docuware_user,
                       'password': self.env.user.company_id.docuware_pass}
        s = requests.Session()
        s.headers.update({'User-Agent': 'welcome-letter'})
        s.headers.update({'Accept': 'application/json'})
        if c_path.exists():
            with open(c_path, mode='rb') as f:
                s.cookies.update(pickle.load(f))

        else:
            url = f'{self.env.user.company_id.docuware_url}/docuware/platform/Account/Logon'
            payload = {
                'LicenseType': '',
                'UserName': credentials['user'],
                'Password': credentials['password'],
                'RedirectToMyselfInCaseOfError': 'false',
                'RememberMe': 'false',
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            print("DEBUG", payload, "=", url)
            response = s.request('POST', url, headers=headers, data=payload, timeout=30)
            print("DEBUG", response)
            if response.status_code == 401:
                logging.info(
                    'Unable to log-in, this could also mean the user is rate limited, locked or user-agent missmatch.')
            response.raise_for_status()
            with open('/opt/odoo/.local/share/Odoo/cookies.bin', mode='wb') as f:
                pickle.dump(s.cookies, f)
            return s
        return s

    #def upload(self, path, fields, s) -> dict:
    #    # upload file, by reusing login cookie
    #    p = Path(path)
    #    file_name = p.name
    #    url = f'{self.env.user.company_id.docuware_url}/docuware/platform/FileCabinets/{self.docuware_cabinet_id}/Documents'
    #    f = []
    #    for key, value in fields.items():
    #        f.append({
    #            'FieldName': key,
    #            'Item': value,
    #            'ItemElementName': 'String',
    #        })

    #    index_json = '{"Fields": ' + json.dumps(f) + '}'
    #    multipart_form_data = {
    #        # name: (filename, data, content_type, headers)
    #        'document': (None, index_json, 'application/json'),
    #        'file[]': (file_name, p.read_bytes(), 'application/pdf'),
    #    }
    #    r = s.request('POST', url, files=multipart_form_data, timeout=30)
    #    r.raise_for_status()
    #    return r.json()

    def logout(self, c_path, s):
        url = f'{self.env.user.company_id.docuware_url}/docuware/platform/Account/Logoff'
        r = s.request('GET', url, timeout=30)
        r.raise_for_status()
        c_path.unlink()

    def get_orgid(self, s):
        url = f'{self.env.user.company_id.docuware_url}/docuware/platform/Organizations'
        resp = s.request('GET', url)
        print('RESP', resp)
        if resp.status_code == 200:
            return json.loads(resp.content.decode('utf-8'))

    def get_all_filecabinets(self, s, OrgId):
        url = f'{self.env.user.company_id.docuware_url}/docuware/platform/FileCabinets?orgid={OrgId}'
        resp = s.request('GET', url)
        if resp.status_code == 200:
            return json.loads(resp.content.decode('utf-8'))

    @api.model
    def sync_cabinets(self):
        try:
            c_path = Path('/opt/odoo/.local/share/Odoo/cookies.bin')
            s = self.login(c_path)
            print("HACE LOGIN")
            res = self.get_orgid(s)
            print("GET ORGID")
            if res:
                for i in range(len(res['Organization'])):
                    if res['Organization'][i]['Name'] == self.env.user.company_id.docuware_organization:
                        print("DEBUG",res['Organization'][i]['Name'])
                        orgid = res['Organization'][i]['Guid']
                if orgid:
                    print("IF ORGID")
                    filecabinets = self.get_all_filecabinets(s, orgid)
                    if filecabinets:
                        print("IF FILECABINETS")
                        docuware_cabinets = self.env['docuware.cabinet'].search([])
                        odoo_cabinets = []
                        for cabinet in docuware_cabinets:
                            odoo_cabinets.append(cabinet.name)
                        for j in range(len(filecabinets['FileCabinet'])):
                            if filecabinets['FileCabinet'][j]['Name'] not in odoo_cabinets:
                                new_cabinet = self.env['docuware.cabinet'].create({
                                    'name': filecabinets['FileCabinet'][j]['Name'],
                                    'guid': filecabinets['FileCabinet'][j]['Id'],
                                })

            self.logout(c_path, s)



        except Exception as e:
            raise UserError("Failed to connect to Docuware Server , please try again later" + str(e))

    def get_filecabinet_documents(self, type):
        if not type:
            type = 'undef'
        try:
            c_path = Path('/opt/odoo/.local/share/Odoo/cookies.bin')
            s = self.login(c_path)

            print("GET CABINET INFO")
            url = f'{self.env.user.company_id.docuware_url}/docuware/platform/FileCabinets/{self.guid}/Documents'
            resp = s.request('GET', url)
            if resp.status_code == 200:
                # return json.loads(resp.content.decode('utf-8'))
                res = json.loads(resp.content.decode('utf-8'))
                docuware_documents = self.env['docuware.document'].search([('cabinet_id', '=', self.id)])
                odoo_documents = []
                for document in docuware_documents:
                    odoo_documents.append(document.name)
                for i in range(len(res['Items'])):
                    print("ITEMS", res['Items'][i]['Title'])
                    if res['Items'][i]['Title'] not in odoo_documents:
                        new_document = self.env['docuware.document'].create({
                            'name': res['Items'][i]['Title'],
                            'cabinet_id': self.id,
                            'document_type': type,
                            #'docuware_cabinet_guid': filecabinets['FileCabinet'][j]['Id'],
                        })
                        for j in range(len(res['Items'][i]['Fields'])):
                            if res['Items'][i]['Fields'][j]['FieldName'] == 'DWDOCID':
                                new_document.document_guid = res['Items'][i]['Fields'][j]['Item']

            self.logout(c_path, s)
        except Exception as e:
            if not self.cabinet_error_log:
                self.cabinet_error_log = str(datetime.now()) + " " + str(e) + "\n"
            else:
                self.cabinet_error_log += str(datetime.now()) + " " + str(e) + "\n"

    def get_default_filecabinet_documents(self):
        self.get_filecabinet_documents('undef')
