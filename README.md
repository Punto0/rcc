# rcc
Red de Compras Colectivas

Proyecto para crear la gestión de una red de compras colectivas a niveles regionales o mayores.

En este momento consta de dos módulos de odoo:

- colective_purchase: Es un módulo que hereda de 'purchase' quitando las restricciones de un único comprador por Purchase Order. Además añade campos y métodos a Purchase Order Line.

- network: Módulo para crear redes entre los 'partners' sean éstas de consumo o de producción. Permite a una red comprar u ofrecer productos como si fuera un parner individual.   

Está previsto integrar éstos módulos en el FairMarket (http://market.fair.coop)

Hay un módulo de pruebas en http://rcc.punto0.org:8069 con los permisos muy relajados para poder cambiar cosas. 

La interfaz xml-rpc se encuentra abierta y se puede testear (crear órdenes, listar producto, añadir líneas a las órdenes, ...), mirar el script en python rcc_test.py para ver un ejemplo.



