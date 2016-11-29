{
    'name': 'Collective Purchase Website',
    'category': 'Website',
    'summary': 'Interfaz web para Collective Purchase',
    'website': '',
    'version': '0.0.1',
    'description': """
Web para las Compras Colectivas
==================

        """,
    'author': 'Red de Compras Colectivas - FairCoop - Punto0',
    'depends': ['website','sale','website_sale','purchase_collective','payment'],
    'data': [
        'data/data.xml',
        'views/views.xml',
        'views/templates.xml',
        #'views/payment.xml',
        #'views/purchase_collective_order.xml',
        'security/ir.model.access.csv',
        'security/website_purchase_collective.xml',
    ],
    #'demo': [
    #    'data/demo.xml',
    #],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
}
