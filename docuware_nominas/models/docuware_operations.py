# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################
from odoo import api, fields, models, _
import pickle, logging, json
import requests
from datetime import datetime
import base64
from requests.structures import CaseInsensitiveDict
from pathlib import Path


class DocuwareOperations(models.Model):
    _inherit = "docuware.operations"

    @api.model
    def get_nominas(self):
        self.env.user.company_id.docuware_cabinet_read_id.get_filecabinet_documents('nomina')

    @api.model
    def get_nominas_data(self):
        c_path = Path('cookies.bin')
        s = self.login(c_path)

        for document in self.env.user.company_id.docuware_cabinet_read_id.docuware_cabinet_document_ids:
            if document.docuware_nomina_done:
                print("Not done")
                print(document.name)
                done = document.get_document_data_from_operation(self.env.user.company_id.mandatory_field_ids, s)
                if done:
                    document.docuware_nomina_done = done
                    signants = document.get_signants()
                    document.write({'partner_ids': [(4, self.env.user.company_id.id)]})

                    line_ids = []
                    for line in document.partner_ids:
                        line_id = self.env['viafirma.lines'].create(
                            {
                                'partner_id': line.id,
                            }
                        )
                        line_ids.append(line_id.id)

                    viafirma = document.viafirma_id = self.env['viafirma'].create({
                        'name': str(document.name),
                        'noti_text': str(document.name),
                        'noti_subject': str(document.name),
                        'template_id': self.env.user.company_id.viafirma_template.id,
                        'notification_type_ids': [(6, 0, self.env.user.company_id.viafirma_notifications.ids)],
                        'line_ids': [(6, 0, line_ids)],
                        'template_type': 'base64',
                        'document_to_send': document.docuware_binary,
                        'res_model': 'docuware.documents',
                        'res_id': document.id,
                        # 'res_id_name': str(self.name),
                        # 'document_policies': False,
                    })
                    if viafirma:
                        stage_id = self.env['docuware.stage'].search([('name', '=', 'Processing')]).id
                        document.stage_id = stage_id
                        document.viafirma_id.call_viafirma()
                    else:
                        stage_id = self.env['docuware.stage'].search([('name', '=', 'Ready')]).id
                        document.stage_id = stage_id

        self.logout(c_path, s)

    @api.model
    def get_signed_nominas(self):
        processing = self.env['docuware.stage'].search([('name', '=', 'Processing')]).id
        signed = self.env['docuware.stage'].search([('name', '=', 'Signed')]).id
        nominas = self.env['docuware.documents'].search([('stage_id', '=', processing)])
        for nomina in nominas:
            if nomina.viafirma_id.document_signed:
                result = nomina.upload()
                if result:
                    nomina.stage_id = signed
                else:
                    nomina.kanban_state_label = nomina.legend_blocked



