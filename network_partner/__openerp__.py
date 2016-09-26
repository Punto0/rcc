# -*- coding: utf-8 -*-
{
    'name': "Network Partner",

    'summary': """
        Network partners""",

    'description': """
Network partners
==================================================

    """,

    'author': "FairCoop",
    'website': "http://market.fair.coop",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ["base", "mail",],

    # always loaded
    'data': [
        #'security/purchase_collective_security.xml',
        #'security/ir.model.access.csv',
        #'data/purchase_collective_workflow.xml',
        #'data/purchase_collective_sequence.xml',
        #'views/purchase_collective.xml',
        'views/res_partner_network.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
