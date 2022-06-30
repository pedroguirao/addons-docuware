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


class DocuwareCabinets(models.Model):
    _inherit = "docuware.cabinet"

    type = fields.Selection(selection_add=[('nominas', 'Nóminas')], ondelete={"nominas": "set null"})
    dictionary_id = fields.Many2one('docuware.dictionary', string='Dictionary')
    # se llamaba mandatory_field_ids
    viafirma_template = fields.Many2one('viafirma.templates', string='Viafirma Template')
    viafirma_notifications = fields.Many2many(
        comodel_name="viafirma.notification",
        string="Notification type",
        domain=[('type', '=', 'notification')],
    )

    @api.model
    def get_nominas(self):
        cabinets = self.env['docuware.cabinet'].search([('type', '=', 'nominas')])
        for cabinet in cabinets:
            cabinet.get_filecabinet_documents('nomina')

    @api.model
    def get_nominas_data(self):
        c_path = Path('/opt/odoo/.local/share/Odoo/cookies.bin')
        print("DEBUG", c_path)
        s = self.login(c_path)
        documents = self.env['docuware.document'].search([('type', '=', 'nominas')])
        for document in documents:
            if document.docuware_nomina_done:
                print("Not done")
                done = document.get_document_data_from_operation(document.cabinet_id.mandatory_field_ids, s)
                try:
                    if done:
                        print("DONE")
                        document.docuware_nomina_done = done
                        # Get partner data to send viafirma notification
                        signants = document.get_signants_test()
                        if signants:
                            # Because is Nomina, we need to add the company in the sign process
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
                                'template_id': document.cabinet_id.viafirma_template.id,
                                'notification_type_ids': [(6, 0,document.cabinet_id.viafirma_notifications.ids)],
                                'line_ids': [(6, 0, line_ids)],
                                'template_type': 'base64',
                                'document_to_send': document.binary,
                                'res_model': 'docuware.documents',
                                'res_id': document.id,
                                # 'res_id_name': str(self.name),
                                # 'document_policies': False,
                            })
                            stage_id = self.env['docuware.stage'].search([('name', '=', 'Ready')]).id
                            document.stage_id = stage_id
                            document.kanban_state = 'done'
                        else:
                            #document.kanban_state_label = document.legend_blocked
                            document.kanban_state = 'blocked'
                            if not document.document_error_log:
                                document.document_error_log = str(datetime.now()) + " " + \
                                                                       "Can't find a user with the given NIF" + "\n"
                                return False
                            else:
                                document.document_error_log += str(datetime.now()) + " " + \
                                                                        "Can't find a user with the given NIF" + "\n"
                                return False
                except Exception as e:
                    #document.kanban_state_label = document.legend_blocked
                    document.kanban_state = 'blocked'
                    if not document.document_error_log:
                        document.document_error_log = str(datetime.now()) + " " + str(e) + "\n"
                    else:
                        document.document_error_log += str(datetime.now()) + " " + str(e) + "\n"
        self.logout(c_path, s)

    @api.model
    def call_viafirma_nominas(self):
        cabinets = self.env['docuware.cabinet'].search([('type', '=', 'nominas')])
        ready = self.env['docuware.stage'].search([('name', '=', 'Ready')]).id
        for cabinet in cabinets:
            nominas = self.env['docuware.document'].search([
                ('stage_id', '=', ready),
                ('cabinet_id', '=', cabinet.id),
            ])
            print("DEBUG", nominas)
            for nomina in nominas:
                try:
                    nomina.viafirma_id.call_viafirma()
                    processing = self.env['docuware.stage'].search([('name', '=', 'Processing')]).id
                    nomina.stage_id = processing
                    nomina.kanban_state = 'done'
                except Exception as e:
                    nomina.kanban_state = 'blocked'
                    if not nomina.document_error_log:
                        nomina.document_error_log = str(datetime.now()) + " " + str(e) + "\n"
                    else:
                        nomina.document_error_log += str(datetime.now()) + " " + str(e) + "\n"

    @api.model
    def get_signed_nominas(self):
        cabinets = self.env['docuware.cabinet'].search([('type', '=', 'nominas')])
        processing = self.env['docuware.stage'].search([('name', '=', 'Processing')]).id
        signed = self.env['docuware.stage'].search([('name', '=', 'Signed')]).id
        for cabinet in cabinets:
            nominas = self.env['docuware.document'].search([
                ('stage_id', '=', processing),
                ('cabinet_id', '=', cabinet.id)
            ])

            for nomina in nominas:
                c_path = Path('/opt/odoo/.local/share/Odoo/cookies.bin')
                s = self.login(c_path)

                if nomina.viafirma_id.document_signed:
                    result = nomina.upload(s)
                    if result:
                        nomina.kanban_state = 'done'
                        nomina.stage_id = signed
                    else:
                        nomina.kanban_state = 'blocked'

                self.logout(c_path, s)
