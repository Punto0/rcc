# -*- coding: utf-8 -*-
{
    'name': "Collective Purchases",

    'summary': """
        Compras colectivas""",

    'description': """
Compras Colectivas 
==================================================

Éste módulo permite a varios usuarios de Odoo realizar una compra de productos a un mismo proveedor o a una 'red de productores', un conjunto de proveedores asociados y con cercanía física que aceptan pedidos conjuntos ahorrando gastos de envío. 

El Usuario que crea la orden es el encargado de distribuir los productos al resto de usuarios, cobrar de ellos y pagar al productor o red.

Notas:
---------------------------------------------------------

* ¿Crear redes de usuarios también? 

* El resto de usuarios pueden añadir líneas de pedido, pero no borrar o editar el resto.       
  
* No hay proceso de pago automático. ¿Es necesario?

    """,

    'author': "FairCoop",
    'website': "http://market.fair.coop",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ["purchase",],

    # always loaded
    'data': [
        'security/purchase_collective_security.xml',
        'security/ir.model.access.csv',
        'data/purchase_collective_workflow.xml',
        'data/purchase_collective_sequence.xml',
        'views/purchase_collective.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
