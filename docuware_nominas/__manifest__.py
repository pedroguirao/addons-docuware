# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2021 Serincloud S.L. All Rights Reserved
#    PedroGuirao pedro@serincloud.com
##############################################################################

{
    "name": "Docuware Nominas",
    "version": "14.0.1.0.0",
    "category": "Documentation and digital sign by viafirma",
    "author": "PedroGuirao",
    "maintainer": "Serincloud",
    "website": "www.ingenieriacloud.com",
    "license": "AGPL-3",
    "depends": [
        'docuware_connector',
        'viafirma',
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/docuware_sync.xml',
        'views/views_models.xml',
        'views/views_menu.xml',
        'data/docuware_automated.xml',
    ],
    "installable": True,
}
