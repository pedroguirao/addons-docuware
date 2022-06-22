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



class ResCompany(models.Model):
    _inherit = "res.company"

    docuware_cabinet_read_id = fields.Many2one('docuware.cabinets', string='Download Cabinet')
    docuware_cabinet_write_id = fields.Many2one('docuware.cabinets', string='Upload Cabinet')
    mandatory_field_ids = fields.One2many('docuware.fields', 'company_id', string='Fields in Docs',
                                help="Mandatory fields to find defined in docuware to download the doc")
    viafirma_template = fields.Many2one('viafirma.templates', string='Viafirma Template')
    viafirma_fields = fields.Many2many('docuware.fields', string='Fields for partner',
                                       help="Fields used to locate the matching User in Odoo must be Odoo NIF, CIF, etc")
    viafirma_notifications = fields.Many2many(
        comodel_name="viafirma.notification",
        string="Notification type",
        domain=[('type', '=', 'notification')],
    )
