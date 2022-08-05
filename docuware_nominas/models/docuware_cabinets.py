# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################

from odoo import api, fields, models, _
from datetime import datetime
from pathlib import Path


class DocuwareCabinets(models.Model):
    _inherit = "docuware.cabinet"

    type = fields.Selection(selection_add=[('nominas', 'Nóminas')], ondelete={"nominas": "set null"})
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
        c_path = Path('/tmp/cookies.bin')
        s = self.login(c_path)
        print("S",s)
        if s:
            stage_id = self.env['docuware.stage'].search([('name', '=', 'New')]).id
            documents = self.env['docuware.document'].search([('type', '=', 'nomina'),('stage_id', '=', stage_id)])
            for document in documents:
                done = document.get_document_data_from_operation(document.cabinet_id.dictionary_id.line_ids, s)
                try:
                    if done:
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
                                'noti_detail': "Document to Sign " + str(document.name),
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
                            document.error_log = str(datetime.now()) + " " + \
                                                                        "Can't find a user with the given NIF" + "\n"
                            return False

                except Exception as e:
                    #document.kanban_state_label = document.legend_blocked
                    document.kanban_state = 'blocked'
                    document.error_log = str(datetime.now()) + " " + str(e) + "\n"
            #self.logout(c_path, s)

    @api.model
    def call_viafirma_nominas(self):
        ready = self.env['docuware.stage'].search([('name', '=', 'Ready')]).id
        nominas = self.env['docuware.document'].search([
            ('stage_id', '=', ready),
            ('type', '=', 'nomina'),
        ])
        for nomina in nominas:
            try:
                nomina.viafirma_id.call_viafirma()
                processing = self.env['docuware.stage'].search([('name', '=', 'Processing')]).id
                nomina.stage_id = processing
                nomina.kanban_state = 'done'
            except Exception as e:
                nomina.kanban_state = 'blocked'
                nomina.error_log = str(datetime.now()) + " " + str(e) + "\n"

    @api.model
    def get_signed_nominas(self):
        processing = self.env['docuware.stage'].search([('name', '=', 'Processing')]).id
        signed = self.env['docuware.stage'].search([('name', '=', 'Signed')]).id
        nominas = self.env['docuware.document'].search([
            ('stage_id', '=', processing),
            ('type', '=', 'nomina'),
        ])
        c_path = Path('/tmp/cookies.bin')
        s = self.login(c_path)
        if s:
            for nomina in nominas:
                if nomina.viafirma_id.document_signed:
                    result = nomina.upload_and_clip(s)
                    if result:
                        nomina.kanban_state = 'done'
                        nomina.stage_id = signed
                    else:
                        nomina.kanban_state = 'blocked'
            #self.logout(c_path, s)
