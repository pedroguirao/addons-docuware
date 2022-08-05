# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################

from odoo import api, fields, models, _
import pickle, logging, json
import requests
from pathlib import Path
from datetime import datetime
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
    dictionary_id = fields.Many2one('docuware.dictionary', string='Dictionary')

    error_log = fields.Text(string='Error log')
    user_ids = fields.Many2many('res.users', string='Users')
    document_count = fields.Integer(string='Docs', compute='get_docs_count')

    def get_docs_count(self):
        docs = self.env['docuware.document'].search([('cabinet_id', '=', self.id)])
        self.document_count = len(docs)

    def login(self, c_path):
        try:
            # Session will hold the cookies
            credentials = {'user': self.env.user.company_id.docuware_user,
                           'password': self.env.user.company_id.docuware_pass}
            s = requests.Session()
            s.headers.update({'User-Agent': 'welcome-letter'})
            s.headers.update({'Accept': 'application/json'})
            if c_path.exists():
                print("exist",s)
                with open(c_path, mode='rb') as f:
                    s.cookies.update(pickle.load(f))
                return s
            else:
                print("DONT",s)
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
                response = s.request('POST', url, headers=headers, data=payload, timeout=30)
                print(response.json())
                print("COOKIES",s.cookies.get_dict())

                if response.status_code != 200:
                    logging.info(
                        'Unable to log-in, this could also mean the user is rate limited, locked or user-agent missmatch.')
                    self.error_log = str(datetime.now()) + " " + str(response.json()) + "\n"
                    return False
                else:
                    with open('/tmp/cookies.bin', mode='wb') as f:
                        pickle.dump(s.cookies, f)
                    return s

        except Exception as e:
            self.error_log = str(datetime.now()) + " " + str(e) + "\n"
            return False

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
        print("RAISE",r.raise_for_status())
        c_path.unlink()

    def get_orgid(self, s):
        url = f'{self.env.user.company_id.docuware_url}/docuware/platform/Organizations'
        resp = s.request('GET', url)
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
            c_path = Path('/tmp/cookies.bin')
            s = self.login(c_path)
            if s:
                res = self.get_orgid(s)
                if res:
                    for i in range(len(res['Organization'])):
                        if res['Organization'][i]['Name'] == self.env.user.company_id.docuware_organization:
                            orgid = res['Organization'][i]['Guid']
                    if orgid:
                        filecabinets = self.get_all_filecabinets(s, orgid)
                        if filecabinets:
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
        try:
            c_path = Path('/tmp/cookies.bin')
            s = self.login(c_path)

            if s:
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
                        if res['Items'][i]['Title'] not in odoo_documents:
                            new_document = self.env['docuware.document'].create({
                                'name': res['Items'][i]['Title'],
                                'cabinet_id': self.id,
                                'type': type,
                            })
                            for j in range(len(res['Items'][i]['Fields'])):
                                if res['Items'][i]['Fields'][j]['FieldName'] == 'DWDOCID':
                                    new_document.guid = res['Items'][i]['Fields'][j]['Item']

                #self.logout(c_path, s)
        except Exception as e:
            self.error_log = str(datetime.now()) + " " + str(e) + "\n"

    def get_default_filecabinet_documents(self):
        if self.type:
            self.get_filecabinet_documents(self.type)
        else:
            self.error_log = str(datetime.now()) + " " + "Cabinet doesn't have type configured" + "\n"
