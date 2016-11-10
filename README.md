# rcc

Red de Compras Colectivas

Proyecto para crear la gestión de una red de compras colectivas a niveles regionales o mayores.

En este momento consta de dos módulos de odoo 8.0 :

* colective_purchase: Es un módulo que hereda de 'purchase' con un campo añadido one2may de sale.order

* network_partner: Módulo para crear redes entre los 'partners' sean éstas de consumo, de producción o ambas. Permite a una red comprar u ofrecer productos como si fuera un parner individual.

* website_purchase_collective: Interfaz web y módulo de ecommerce. 

Está previsto integrar éstos módulos en el FairMarket (http://market.fair.coop).

Hay un módulo de pruebas en http://rcc.punto0.org:8069 con los permisos muy relajados para poder cambiar cosas. 

La interfaz xml-rpc se encuentra abierta y se puede testear (crear órdenes, listar producto, añadir líneas a las órdenes, ...), mirar el script en python xmlrpc_test.py para ver un ejemplo en python.

Modificando la web:

Las plantillas tiene accesos a todos los campos de los modelos. Ver la plantilla actual para ver cómo acceder a esos datos.

La plantilla xml de las páginas se encuentran en website_purchase_collective/views/templates.xml. Siguiendo el flujo normal de la orden corresponden: 

    -- Página de entrada al módulo, listado de las órdenes abiertas: /collective_purchase/open
            <template id="request_quotations" name="Request Quotations"> línea 1124

     -- Página de una orden individual: /collective_purchase/order/#
            <template id="orders_followup" name="Purchase Order"> línea 1185
            Esta página llama a la plantilla del carro, que está integrado en la página:
            <template id="cart" name="Shopping Cart"> línea 1281
            Esta plantilla ejecuta javascript en Website_purchas_collective/src/js/website_purchase.js
    
     -- Página de checkout /purchase/checkout -- Formulario para info del comprador
            <template id="checkout"> linea 703
    
     -- Página de pago /purchase/payment -- Confirmar y elegir la forma de pago:
            <template id="payment"> linea 882
            Esta plantilla ejecuta javascript en webite_purchase_collective/src/js/website_payment.js
            Después de esto se redirige a la página correspondiente del módulo de pago elegido.
            
            
            
            

