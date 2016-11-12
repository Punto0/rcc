# -*- coding: utf-8 -*-
{
    'name': "Collective Purchases",

    'summary': """
        Compras colectivas""",

    'description': """
Compras Colectivas 
==================================================

Éste módulo permite a varios usuarios de Odoo realizar una compra de productos a un mismo proveedor que acepta pedidos conjuntos.

El Usuario que crea la orden es el encargado de distribuir los productos al resto de usuarios, cobrar de ellos y pagar al productor.

    """,

    'author': "Red de Compras Colectivas - FairCoop - Punto0",
    'website': "http://market.fair.coop",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ["purchase","sale","product",],

    # always loaded
    'data': [
        'security/purchase_collective_security.xml',
        'security/ir.model.access.csv',
        'data/purchase_collective_workflow.xml',
        'data/purchase_collective_sequence.xml',
        'views/purchase_collective.xml',
        'views/product.xml',
        'views/sale_order.xml',  
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo.xml',
    #],
    'installable': True,
    'auto_install': False,
    'application': True,
}
