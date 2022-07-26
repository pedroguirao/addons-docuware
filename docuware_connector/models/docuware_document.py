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

TYPES = [
    ('undef', 'Undefined'),
]

class DocuwareDocument(models.Model):
    _name = "docuware.document"
    _description = "Documents to work with Odoo and Apps"

    name = fields.Char(string='Name')
    cabinet_id = fields.Many2one('docuware.cabinet', string='Cabinet')
    guid = fields.Char(string='Document Guid')
    error_log = fields.Text(string="Error log")

    json = fields.Text("Server Json")
    binary = fields.Binary("Original")
    value_ids = fields.One2many('docuware.value', 'document_id', string='Fields')
    type = fields.Selection(selection=TYPES, string='Document type')

    kanban_state = fields.Selection([
        ('done', 'Done'),
        ('blocked', 'Blocked')], string='Kanban State',
        copy=False, default='done', required=True)
    kanban_state_label = fields.Char(compute='_compute_kanban_state_label', string='Kanban State Label', tracking=True)
    legend_blocked = fields.Char(
        'Red Kanban Label', default=lambda s: _('Blocked'), translate=True, required=True,
        help='Override the default value displayed for the blocked state for kanban selection, when the task or issue is in that stage.')
    legend_done = fields.Char(
        'Green Kanban Label', default=lambda s: _('Done'), translate=True, required=True,
        help='Override the default value displayed for the done state for kanban selection, when the task or issue is in that stage.')

    def _default_stage(self):
        return self.env['docuware.stage'].search([('name', '=', 'New')], limit=1).id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['docuware.stage'].search([])
        return stage_ids

    stage_id = fields.Many2one('docuware.stage', string='Stage', store=True, readonly=False, ondelete='restrict',
                               tracking=True, index=True, group_expand='_read_group_stage_ids', copy=False,
                               default=_default_stage)

    @api.depends('stage_id', 'kanban_state')
    def _compute_kanban_state_label(self):
        for doc in self:
            if doc.kanban_state == 'blocked':
                doc.kanban_state_label = doc.legend_blocked
            else:
                doc.kanban_state_label = doc.legend_done

    ### Show information sent by docuware about document, just for debug ###
    def get_document_data(self):
        c_path = Path('/tmp/cookies.bin')
        credentials = {'user': self.env.user.company_id.docuware_user,
                       'password': self.env.user.company_id.docuware_pass}
        s = self.cabinet_id.login(credentials, c_path)

        for document in self:
            try:
                url = f'{self.env.user.company_id.docuware_url}' \
                      f'/docuware/platform/FileCabinets/{document.docuware_cabinet_id.guid}' \
                      f'/Documents/{document.guid}'
                resp = s.request('GET', url)

                if resp.status_code == 200:
                    # return json.loads(resp.content.decode('utf-8'))
                    res = json.loads(resp.content.decode('utf-8'))
                    for i in range(len(res['Fields'])):
                        print(res['Fields'][i]['FieldName'])

            except Exception as e:
                document.error_log = str(datetime.now()) + " " + str(e) + "\n"
        self.cabinet_id.logout(c_path, s)

    def generate_attachment(self, s, img_url):
        if img_url:
            url = f'{self.env.user.company_id.docuware_url}' \
                  f'{img_url}'
            response = s.request('GET', url)
            if response.status_code == 200:
                return base64.b64encode(response.content)
        else:
            self.kanban_state_label = self.legend_blocked
            self.error_log = str(datetime.now()) + " " + "No document received" + "\n"

    def get_document_data_from_operation(self, fields, s):
        try:
            url = f'{self.env.user.company_id.docuware_url}' \
                  f'/docuware/platform/FileCabinets/{self.cabinet_id.guid}' \
                  f'/Documents/{self.guid}'
            resp = s.request('GET', url)

            if resp.status_code == 200:
                res = json.loads(resp.content.decode('utf-8'))
                mandatory = []
                fdownload = False

                for j in range(len(res['Links'])):
                    if res['Links'][j]['rel'] == "fileDownload":
                        fdownload = res['Links'][j]['href']
                self.json = res

                for f in fields:
                    for i in range(len(res['Fields'])):
                        if res['Fields'][i]['FieldName'] == f.name:
                            mandatory.append(f.name)
                            exist_field = self.env['docuware.value'].sudo().search(
                                [('name', '=', res['Fields'][i]['FieldName']), ("document_id", "=", self.id)], limit=1)
                            if not exist_field:
                                self.env['docuware.value'].create(
                                    {'name': res['Fields'][i]['FieldName'],
                                     'value': res['Fields'][i]['Item'],
                                     'document_id': self.id,
                                     'odoo_field_id': f.odoo_field_id,
                                     })
                if len(mandatory) == len(fields):
                    self.binary = self.generate_attachment(s, fdownload)
                    return True
                else:
                    self.kanban_state_label = self.legend_blocked
                    self.error_log = str(datetime.now()) + " " + "Need more fields in docuware " \
                                                                                       "to complete operation" + "\n"
                    return False
        except Exception as e:
            self.error_log = str(datetime.now()) + " " + str(e) + "\n"
            return False



