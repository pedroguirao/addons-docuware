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


class DocuwareOperations(models.Model):
    _name = "docuware.operations"
    _description = "Methods to connect , upload and download documents"

    name = fields.Char(string='Name')
    #cabinet_read_id = fields.Many2one('docuware.cabinets', string='Download Cabinet')
    #cabinet_write_id = fields.Many2one('docuware.cabinets', string='Upload Cabinet')
    #field_ids = fields.One2many('docuware.fields','operation_id', string='Fields in Docs',
    #                            help="Mandatory fields to find defined in docuware to download the doc")

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
            response = s.request('POST', url, headers=headers, data=payload, timeout=30)
            if response.status_code == 401:
                logging.info(
                    'Unable to log-in, this could also mean the user is rate limited, locked or user-agent missmatch.')
            response.raise_for_status()
            with open('/opt/odoo14/.local/share/Odoo/cookies.bin', mode='wb') as f:
                pickle.dump(s.cookies, f)
            return s
        return s

    def logout(self, c_path, s):
        url = f'{self.env.user.company_id.docuware_url}/docuware/platform/Account/Logoff'
        r = s.request('GET', url, timeout=30)
        r.raise_for_status()
        c_path.unlink()
