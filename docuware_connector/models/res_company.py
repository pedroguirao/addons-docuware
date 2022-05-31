# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################
from odoo import api, fields, models, _


class DocuwareConfig(models.Model):
    _inherit = "res.company"

    #name = fields.Char(string='Name')
    docuware_organization = fields.Char(string='Name')
    docuware_url = fields.Char(string='URL')
    docuware_user = fields.Char(string='User')
    docuware_pass = fields.Char(string='Password')


